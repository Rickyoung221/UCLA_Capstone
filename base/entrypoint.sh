#!/usr/bin/bash

# Set JAVA_HOME at runtime so it works on both amd64 and arm64 (e.g. Mac M1)
export JAVA_HOME=$(ls -d /usr/lib/jvm/java-8-openjdk-* 2>/dev/null | head -1)
[ -n "${JAVA_HOME}" ] && export PATH="${JAVA_HOME}/bin:${PATH}"

exec "$@"