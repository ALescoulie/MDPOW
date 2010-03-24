#!/bin/bash

# XXX: would be nice to get version from setup.py and patch it into
# XXX: doc/sphinx/source/conf.py

PACKAGE=POW
EPYDOC_DIRS="mdpow"

SERVERDIR=/sansom/public_html/sbcb/oliver
PACKAGES=$SERVERDIR/download/Python
DOCS=$SERVERDIR/software/$PACKAGE

COPY=0

usage="usage: $0 [OPTIONS] [cmd1 cmd2 ...]

Build distribution and python packages for $PACKAGE 
and copy files to the server directory (must be nfs mounted). 

default commands: 'distribution docs'

cmd           description
-----         -----------------
distribution  make sdist and egg, ##copy to $PACKAGES
docs          'make_epydoc make_sphinx'
make_epydoc   source code docs, copy to $DOCS/epydoc
make_sphinx   documentation, copy to $DOCS/html


Options

-h           help
-c           publish on server (copy) [$COPY]
-n           do not copy              [$((1-COPY))]
-s DIR       server dir [${SERVERDIR}]
-p VERSION   python version, eg 2.5
"

function die () {
    echo 1>&2 "ERROR: $1"
    exit ${2:-1}
}

RSYNC () {
  if [ $COPY = 1 ]; then
      rsync $*;
  fi
}

distribution () {
  $PYTHON setup.py sdist \
      && $PYTHON setup.py bdist_egg \
      && RSYNC -v --checksum dist/* $PACKAGES \
      || die "Failed distribution"
}

make_epydocs() {
  epydoc -v -o doc/epydoc --html --name=$PACKAGE \
         --url=http://sbcb.bioch.ox.ac.uk/oliver/software/$PACKAGE/ \
         ${EPYDOC_DIRS}  \
      || die "Failed making epydoc"
  RSYNC -vrP --delete doc/epydoc $DOCS
}

make_sphinx () {
  (cd doc/sphinx && make clean && make html) || die "Failed making sphinx docs"
  RSYNC -vrP --delete doc/sphinx/build/html $DOCS
}

docs () {
  make_epydocs 
  make_sphinx
}


echo "COPY disabled for the time being ($PACKAGE not released yet, force with -c)"
while getopts hns:p: OPT; do
    case "$OPT" in
	h) echo "$usage"; exit 0;;
	n) COPY=0;;
	c) COPY=1;;
	s) SERVERDIR=$OPTARG;;
	p) PYVERSION=$OPTARG;;
	[?]) echo "Illegal option. See -h for usage.";
	     exit 1;;
    esac
done
shift $((OPTIND-1))


PACKAGES=$SERVERDIR/download/Python
DOCS=$SERVERDIR/software/$PACKAGE

case "$PYVERSION" in
   2.5|2.5.*)  PYTHON=python2.5;;
   2.6|2.6.*)  PYTHON=python2.6;;
   2.[0-4])    die "pyversion $PYVERSION not supported";;
   *)          PYTHON=python;;
esac

commands="$@"
[ -n "$commands" ] || commands="distribution docs"

for cmd in $commands; do
    eval "$cmd"
done

