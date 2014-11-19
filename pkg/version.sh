#!/bin/bash
DIR=$(cd $(dirname "$0"); pwd)
echo raspberrystemtest > $DIR/NAME
git describe --tags --dirty > $DIR/VERSION

