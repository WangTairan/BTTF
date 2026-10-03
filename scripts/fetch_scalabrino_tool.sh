#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DESTINATION="${ROOT_DIR}/src/methods/scalabrino/official_tool"
URL="https://dibt.unimol.it/report/readability/files/readability.zip"
ARCHIVE_SHA256="e556b9b05ed14ed76c122170bd7d43fbc39cf80b8acac2930caebe96ac284329"
JAR_SHA256="2df38f4fecaf84806f5600329ff7eea53fad11ed47892c973e6932c189790b92"
CLASSIFIER_SHA256="5a3ec858d5abc0b28a62070a892f52b58eaacf530ff091b01e579de1c2beab4d"

for command in curl unzip shasum; do
  command -v "${command}" >/dev/null || {
    echo "Required command not found: ${command}" >&2
    exit 1
  }
done

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/scalabrino.XXXXXX")"
trap 'rm -rf "${temporary_directory}"' EXIT
archive="${temporary_directory}/readability.zip"

curl --fail --location --output "${archive}" "${URL}"
printf '%s  %s\n' "${ARCHIVE_SHA256}" "${archive}" | shasum -a 256 --check

mkdir -p "${DESTINATION}"
unzip -j -o "${archive}" rsm.jar readability.classifier -d "${DESTINATION}"
printf '%s  %s\n' "${JAR_SHA256}" "${DESTINATION}/rsm.jar" | shasum -a 256 --check
printf '%s  %s\n' "${CLASSIFIER_SHA256}" \
  "${DESTINATION}/readability.classifier" | shasum -a 256 --check

echo "Scalabrino assets installed in ${DESTINATION}"
