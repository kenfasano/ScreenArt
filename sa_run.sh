#!/bin/zsh

# --- 1. Set Defaults ---
NUM_TIMES=1
DEFAULT_MAX_LOOP=10
SLEEP_SECONDS=3    #600

# Note the leading colon inside the quotes
while getopts ":n:s:" opt; do
	case ${opt} in
		n) NUM_TIMES=${OPTARG} ;;
		s) SLEEP_SECONDS=${OPTARG} ;;
		\?) break ;; # Stop parsing on unknown options
	esac
done

# Shift past the options we just parsed
shift $((OPTIND -1))
EXTRA_ARGS="$@"

if [ -z "${NUM_TIMES}" ]; then
	NUM_TIMES=$DEFAULT_MAX_LOOP
	echo "Starting ScreenArt loop infinitely with ${SLEEP_SECONDS}s sleep..."
else
	echo "Starting ScreenArt loop with ${NUM_TIMES} iterations and ${SLEEP_SECONDS}s sleep..."
fi

if [[ "$OSTYPE" == "linux"* ]]; then
	SCRIPTS=~/mac/Scripts
else
	SCRIPTS=~/Scripts
fi

#
# Run Loop
i=0
while true; do
	i=$((i+1))

	echo "-----------------------------------"
	echo "Run ${i} of ${NUM_TIMES} - $(date)"
	echo "-----------------------------------"

	cd $SCRIPTS/ScreenArt
	echo "sa_run.sh: Running ./current.sh"
	./current.sh $EXTRA_ARGS
	rc=$?
	echo "sa_run.sh: current.sh rc=$rc"

	# Exit if we've hit the requested number of runs
	if [ $i -eq 0 ]; then
		echo "sa_run.sh: Loop complete."
		break
	fi

	# Sleep if we're not in infinite loop
	if [ $i -ne $NUM_TIMES ]; then
		echo "sa_run.sh: ./current.sh succeeded. Waiting for ${SLEEP_SECONDS}s..."
		sleep "${SLEEP_SECONDS}"
	else
		break
	fi
done

echo "rc=$rc"
exit $rc
