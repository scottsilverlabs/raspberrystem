/*
 * Copyright (c) 2015  Brian Silverman <bri@raspberrystem.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <malloc.h>
#include <unistd.h>
#include <stdlib.h>
#include <assert.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <alsa/asoundlib.h>
#include <pthread.h>

//
// Fixed formats.  AUDIO_BUFFER_SIZE must be large enough to avoid underruns,
// but small enough to have minimal latency.
//
#define AUDIO_FORMAT      SND_PCM_FORMAT_S16_LE
#define AUDIO_SPEED       44100
#define AUDIO_CHANNELS    1
#define AUDIO_BUFFER_SIZE 4096

#define MAX_PLAYERS         8
#define MAX_AUDIO_BUF       1024

#define NONE    0
#define START   1
#define MIDDLE  2
#define END     3

static snd_pcm_t *handle;
static snd_pcm_uframes_t chunk_size = 0;
static size_t bits_per_sample, bits_per_frame;
static size_t chunk_bytes;
static int client_sockets[MAX_PLAYERS];
static short client_buffers1[MAX_PLAYERS][MAX_AUDIO_BUF];
static short client_buffers2[MAX_PLAYERS][MAX_AUDIO_BUF];
static pthread_mutex_t mutex;

//
// Read up to count bytes on file descriptor.  Accounts for partial reads.
//
static ssize_t full_read(int fd, void *buf, size_t count)
{
    ssize_t bytes_read = 0, ret;

    while (count > 0) {
        if ((ret = read(fd, buf, count)) == 0)
            break;
        if (ret < 0)
            return bytes_read > 0 ? bytes_read : ret;
        count -= ret;
        bytes_read += ret;
        buf = (char *)buf + ret;
    }
    return bytes_read;
}


static void configure_audio(void)
{
    char * pcm_name = "default";
    snd_pcm_hw_params_t *params;
    int err;

    err = snd_pcm_open(&handle, pcm_name, SND_PCM_STREAM_PLAYBACK, 0);
    if (err < 0) {
        exit(EXIT_FAILURE);
    }

    snd_pcm_hw_params_alloca(&params);

    err = snd_pcm_hw_params_any(handle, params);
    err = err || snd_pcm_hw_params_set_access(handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
    err = err || snd_pcm_hw_params_set_format(handle, params, AUDIO_FORMAT);
    err = err || snd_pcm_hw_params_set_channels(handle, params, AUDIO_CHANNELS);
    err = err || snd_pcm_hw_params_set_rate(handle, params, AUDIO_SPEED, 0);
	err = err || snd_pcm_hw_params_set_buffer_size(handle, params, AUDIO_BUFFER_SIZE);
    err = err || snd_pcm_hw_params(handle, params);
    if (err < 0) {
        exit(EXIT_FAILURE);
    }

    snd_pcm_hw_params_get_period_size(params, &chunk_size, 0);
    bits_per_sample = snd_pcm_format_physical_width(AUDIO_FORMAT);
    bits_per_frame = bits_per_sample * AUDIO_CHANNELS;
    chunk_bytes = chunk_size * bits_per_frame / 8;
    assert(chunk_size < MAX_AUDIO_BUF);
}


//
// Write up to count frames on audio handle.  Accounts for partial writes.
//
static ssize_t pcm_write(u_char *data, size_t count)
{
    ssize_t r;
    ssize_t result = 0;

    while (count > 0) {
        r = snd_pcm_writei(handle, data, count);
        if (r == -EAGAIN || (r >= 0 && (size_t)r < count)) {
            snd_pcm_wait(handle, 100);
        } else if (r == -EPIPE) {
            snd_pcm_recover(handle, r, 0);
        } else if (r < 0) {
            exit(EXIT_FAILURE);
        }
        if (r > 0) {
            result += r;
            count -= r;
            data += r * bits_per_frame / 8;
        }
    }
    return result;
}


//
// Triangular time window for pop suppresion.
//
static inline float window(int pos, int i)
{
    if (pos == MIDDLE) return 1.0;

    if (pos == START) {
        return (float) i / chunk_size;
    } else { // Must be END
        return (float) (chunk_size - i) / chunk_size;
    }
}


//
// mixer() thread mixes incoming audio bufs from multiple sockets and outputs to ALSA.
//
void * mixer()
{
    char eof;
    int read_size;
    int r;
    int i, j;
    short (*pcurrbufs)[MAX_PLAYERS][MAX_AUDIO_BUF];
    short (*pprevbufs)[MAX_PLAYERS][MAX_AUDIO_BUF];
    short outbuf[MAX_AUDIO_BUF];
    int audio_mix_buf[MAX_AUDIO_BUF];
    struct {
        int count;
        float gain;
    } header;
    int broken_socket;
    int count;
    int client_position[MAX_PLAYERS];
    float prev_gain[MAX_PLAYERS];
    float curr_gain[MAX_PLAYERS];

    signal(SIGPIPE, SIG_IGN);

    pcurrbufs = &client_buffers1;
    pprevbufs = &client_buffers2;

    for(;;) {
        //
        // Run through list of connected sockets - for each one, read an audio
        // buffer.
        //
        // Must use client_sockets[] array mutex-ly
        //
        // To support time-windowing for pop-suppression, we delay audio by one
        // frame (using ping-pong buffers).  We need to be one buffer delayed
        // so that we can modify the previous buffer if the connection ends
        // abruptly (e.g., by error).
        //
        pthread_mutex_lock(&mutex);
        for (i = 0; i < MAX_PLAYERS; i++) {
            client_position[i] = NONE;
            if (client_sockets[i]) {
                broken_socket = 0;
                eof = 0;

                //
                // Read header
                //
                r = full_read(client_sockets[i], &header, sizeof(header));
                if (r <= 0) {
                    broken_socket = 1;
                } else {
                    eof = header.count < 0;
                }

                //
                // Read audio buffer (if given)
                //
                if (! (eof || broken_socket)) {
                    r = full_read(client_sockets[i], (*pcurrbufs)[i], chunk_bytes);
                    if (r <= 0) {
                        broken_socket = 1;
                    }
                }

                //
                // ACK client
                //
                if (! broken_socket) {
                    r = write(client_sockets[i], &eof, 1);
                    if (r < 0 && errno == EPIPE) {
                        broken_socket = 1;
                    }
                }
                if (eof || broken_socket) {
                    close(client_sockets[i]);
                    client_sockets[i] = 0;
                }

                //
                // Save position of buffer in stream (unstarted/start/middle/end)
                //
                if (eof || broken_socket) {
                    client_position[i] = END;
                } else if (header.count > 1) {
                    client_position[i] = MIDDLE;
                } else if (header.count == 1) {
                    client_position[i] = START;
                }
                prev_gain[i] = curr_gain[i];
                curr_gain[i] = header.gain;
            }
        }

        //
        // Mix audio buffers.  Use (int) mix buffer to avoid overflow
        //
        // Audio is mixed with user supplied gain, and start/end bufferes are
        // time windowed for pop-suppresion.  
        //
        memset(audio_mix_buf, 0, chunk_size * sizeof(int));
        count = 0;
        for (i = 0; i < MAX_PLAYERS; i++) {
            if (client_position[i]) {
                count++;
                for (j = 0; j < chunk_size; j++) {
                    audio_mix_buf[j] += 
                        (*pprevbufs)[i][j] 
                        * prev_gain[i]
                        * window(client_position[i], j);
                }
            }
        }
        pthread_mutex_unlock(&mutex);

        //
        // If there's a mixed audio buf, send it to ALSA.
        //
        if (count) {
            //
            // Convert int mix to short.
            //
            for (j = 0; j < chunk_size; j++) {
                register unsigned int high_short = ((unsigned int) audio_mix_buf[j]) >> 15;
                if (high_short == 0x0001FFFF || high_short == 0x00000000) {
                    outbuf[j] = audio_mix_buf[j];
                } else if (high_short & 0x10000) {
                    outbuf[j] = 0x8000;
                } else {
                    outbuf[j] = 0x7FFF;
                }
            }

            //
            // Write audio - should not fail (catastrophic failure cause
            // pcm_write() to exit().
            //
            r = pcm_write((u_char *) outbuf, chunk_size);
            assert(r == chunk_size);
        }
        usleep(2000);

        //
        // Flip buffers
        //
        void * p;
        p = pprevbufs;
        pprevbufs = pcurrbufs;
        pcurrbufs = p;
    }

    // Should never exit, but exit cleanly just in case
    pthread_exit((void*) 0);
}


//
// socket_server() listens for client socket requests, and passes sockets to mixer() thread.
//
void * socket_server()
{
    int i;
    int server_fd, client_fd, c;
    struct sockaddr_in server, client;
    char client_message[2000];

    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("socket()");
        exit(EXIT_FAILURE);
    }

    // Prepare the sockaddr_in structure
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons( 8888 );

    // Bind
    int yes = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
        perror("setsockopt()");
        exit(EXIT_FAILURE);
    }
    if (bind(server_fd,(struct sockaddr *)&server, sizeof(server)) < 0) {
        perror("bind()");
        exit(EXIT_FAILURE);
    }

    // Listen
    listen(server_fd, MAX_PLAYERS);

    // Accept connection from an incoming client
    for (;;) {
        printf("Waiting for incoming connections...\n");
        c = sizeof(struct sockaddr_in);

        while( (client_fd = accept(server_fd, (struct sockaddr *)&client, (socklen_t*)&c)) )
        {
            printf("Connection accepted, %d\n", client_fd);

            //
            // "Send" client sockets to mixer thread
            //
            pthread_mutex_lock(&mutex);
            for (i = 0; i < MAX_PLAYERS; i++) {
                if (client_sockets[i] == 0) {
                    client_sockets[i] = client_fd;
                    break;
                }
            }
            if (i >= MAX_PLAYERS) {
                printf("Player limit reached\n");
                close(client_fd);
            }
            pthread_mutex_unlock(&mutex);

            printf("Waiting for next connection\n");
        }

        // Shouldn't reach here - but if we do, just throttle and try again
        sleep(1);
    }

    // Should never exit, but exit cleanly just in case
    pthread_exit((void*) 0);
}


int main(int argc, char *argv[])
{
    pthread_t mixer_tid, socket_server_tid;

    pthread_mutex_init(&mutex, NULL);

    configure_audio();

    if (pthread_create(&mixer_tid, NULL,  mixer, 0) < 0) {
        exit(EXIT_FAILURE);
    }

    if (pthread_create(&socket_server_tid, NULL,  socket_server, 0) < 0) {
        exit(EXIT_FAILURE);
    }

    //
    // Currently, worker threads never exit, so we should never reach here.
    //
    pthread_join(mixer_tid, NULL);
    pthread_join(socket_server_tid, NULL);

    snd_pcm_nonblock(handle, 0);
    snd_pcm_drain(handle);
    snd_pcm_close(handle);
    snd_config_update_free_global();

    pthread_mutex_destroy(&mutex);

    return 0;
}


