#!/opt/homebrew/bin/zsh
HOUR=$(date +%H)

echo "PROFILING TRANSFORMERS ($(date))..."

# Change the directory to the parent folder of the Transformers package
cd "/Users/kenfasano/Scripts/"

rm -f Transformers/Transformers.err

PYTHON='/Library/Frameworks/Python.framework/Versions/3.13/bin/python3'
only=""

# Define the options that getopts should look for
# The colon after a letter indicates that the option expects an argument
# In this case, 'opk' means it looks for -k, -o, -p
while getopts "op" opt; do
  case $opt in
    o)
      echo "Got O"
      only="ONLY"
      ;;
    ?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# The 'shift' command discards the options that have been processed by getopts
shift $((OPTIND-1))

timestamp=$(date +%Y%m%d_%H%M%S)
profile_filename="Transformers/profile_output_${timestamp}.prof"
# Run run_.py as a module within the 'Transformers' package
$PYTHON -m cProfile -o "$profile_filename" -m Transformers.run "$only"
rc=$?
if [[ $rc -eq 0 ]]; then
    echo "Done. Recreated TRANSFORMERS. rc=$rc"
else
    echo "Failed. rc=$rc"
    exit 1
fi

# Run snakeviz to visualize the profiling data
# This will open a web browser with an interactive visualization
echo "Launching snakeviz..."
snakeviz "$profile_filename"

echo "Done. snakeviz launched. rc=$rc"
exit 0
