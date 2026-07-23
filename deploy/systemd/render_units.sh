#!/usr/bin/env bash
set -euo pipefail

error() {
  printf '%s\n' "$1" >&2
  exit 2
}

env_root_is_set=${PLA_DEPLOY_ROOT+x}
deploy_root=${PLA_DEPLOY_ROOT-}
arg_root_is_set=
output_dir=

while (($#)); do
  case $1 in
    --deploy-root)
      [[ -z $arg_root_is_set ]] || error "--deploy-root may be supplied only once"
      (($# >= 2)) || error "--deploy-root requires a value"
      arg_root_is_set=1
      deploy_root=$2
      shift 2
      ;;
    --output-dir)
      [[ -z $output_dir ]] || error "--output-dir may be supplied only once"
      (($# >= 2)) || error "--output-dir requires a value"
      output_dir=$2
      shift 2
      ;;
    *)
      error "unsupported argument: $1"
      ;;
  esac
done

if [[ -n $arg_root_is_set && -n $env_root_is_set ]]; then
  error "supply deployment root using either --deploy-root or PLA_DEPLOY_ROOT, not both"
fi
[[ -n $arg_root_is_set || -n $env_root_is_set ]] || error "PLA_DEPLOY_ROOT is required"
[[ -n $deploy_root ]] || error "deployment root must not be empty"
[[ -n $output_dir ]] || error "--output-dir is required"
[[ $deploy_root == /* ]] || error "deployment root must be absolute"
[[ $deploy_root =~ ^/[A-Za-z0-9._/-]+$ ]] || error "deployment root contains unsupported characters"
[[ $deploy_root != *//* ]] || error "deployment root must be normalized"
[[ $deploy_root != */./* && $deploy_root != */../* ]] || error "deployment root must be normalized"
[[ $deploy_root != */. && $deploy_root != */.. ]] || error "deployment root must be normalized"
[[ $deploy_root == / || $deploy_root != */ ]] || error "deployment root must be normalized"

case $deploy_root in
  /home/pla/hexforge-pla|/home/pla/hexforge-pla/*|\
  /home/devuser/hexforge-pla-hf-p0-002|/home/devuser/hexforge-pla-hf-p0-002/*|\
  */hexforge-ai-ops|*/hexforge-ai-ops/*)
    error "forbidden deployment root"
    ;;
esac

[[ ! -e $deploy_root/.git ]] || error "deployment root must not be a source repository"
[[ -d $deploy_root/pla_node ]] || error "deployment root is missing required component: pla_node"
[[ -d $deploy_root/software/brain_receiver ]] || error "deployment root is missing required component: software/brain_receiver"
[[ -d $output_dir ]] || error "output directory must already exist"
[[ ! -L $output_dir ]] || error "output directory must not be a symbolic link"

shopt -s nullglob dotglob
output_entries=("$output_dir"/*)
((${#output_entries[@]} == 0)) || error "output directory must be empty"
shopt -u nullglob dotglob

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/../.." && pwd)
names=(pla-node.service brain-receiver.service)
templates=(
  "$repo_root/pla_node/deploy/pla-node.service.in"
  "$script_dir/brain-receiver.service.in"
)
temporary_files=("$output_dir/.pla-node.service.tmp" "$output_dir/.brain-receiver.service.tmp")
final_files=("$output_dir/pla-node.service" "$output_dir/brain-receiver.service")

cleanup() {
  rm -f -- "${temporary_files[@]}"
  if [[ ${publish_started:-0} == 1 ]]; then
    rm -f -- "${final_files[@]}"
  fi
}
trap cleanup EXIT HUP INT TERM

for index in 0 1; do
  template=${templates[$index]}
  temporary=${temporary_files[$index]}
  [[ -f $template ]] || error "unit template is missing: ${names[$index]}.in"
  sed "s|@PLA_DEPLOY_ROOT@|$deploy_root|g" "$template" >"$temporary"
  grep -Fq '@PLA_DEPLOY_ROOT@' "$temporary" && error "unresolved deployment-root placeholder"
  grep -Fq '/home/pla/hexforge-pla' "$temporary" && error "historical deployment root remains"
  grep -Fq '/home/devuser/hexforge-pla-hf-p0-002' "$temporary" && error "development-clone path remains"
done

publish_started=1
for index in 0 1; do
  mv -- "${temporary_files[$index]}" "${final_files[$index]}"
done
publish_started=0
trap - EXIT HUP INT TERM
printf 'Rendered %s and %s\n' "${final_files[0]}" "${final_files[1]}"
