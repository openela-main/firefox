#!/usr/bin/bash


function run_tests_wayland {
  # usage: run-tests-wayland [test flavour]

  set -x

  RUN_XPCSHELL_TEST=1
  RUN_REFTEST=1
  RUN_MOCHITEST=1
  RUN_CRASHTEST=1

  while (( "$#" )); do
    SELECTED_TEST=$1
    if [ "$SELECTED_TEST" = "xpcshell" ] ; then
      RUN_XPCSHELL_TEST=1
    elif [ "$SELECTED_TEST" = "reftest" ] ; then
      RUN_REFTEST=1
    elif [ "$SELECTED_TEST" = "mochitest" ] ; then
      RUN_MOCHITEST=1
    elif [ "$SELECTED_TEST" = "crashtest" ] ; then
      RUN_CRASHTEST=1
    fi
    shift
  done

  export MACH_USE_SYSTEM_PYTHON=1
  export MOZ_NODE_PATH=/usr/bin/node

  MOCHITEST_PARAMS="--timeout 1 --chunk-by-dir 4"
  TEST_DIR="test_results"
  mkdir $TEST_DIR

  env | grep "DISPLAY"

  # Fix for system nss
  ln -s /usr/bin/certutil objdir/dist/bin/certutil
  ln -s /usr/bin/pk12util objdir/dist/bin/pk12util

  NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"

  export MOZ_ENABLE_WAYLAND=1

  if [ $RUN_XPCSHELL_TEST -ne 0 ] ; then
  #  ./mach xpcshell-test 2>&1 | cat - | tee $TEST_DIR/xpcshell
    ./mach xpcshell-test --enable-webrender 2>&1 | cat - | tee $TEST_DIR/xpcshell-wr
    sleep 60
  fi

  # Basic render testing
  export TEST_PARAMS="--setpref reftest.ignoreWindowSize=true --setpref widget.wayland.test-workarounds.enabled=true"
  #export TEST_FLAVOUR=""
  #if [ $RUN_REFTEST -ne 0 ] ; then
  #  ./mach reftest --marionette localhost:$(($(($RANDOM))+2000)) $TEST_PARAMS 2>&1 | tee $TEST_DIR/reftest$TEST_FLAVOUR
  #fi
  #if [ $RUN_CRASHTEST -ne 0 ] ; then
  #  ./mach crashtest --marionette localhost:$(($(($RANDOM))+2000)) $TEST_PARAMS 2>&1 | tee $TEST_DIR/crashtest$TEST_FLAVOUR
  #fi
  #if [ $RUN_MOCHITEST -ne 0 ] ; then
  #  ./mach mochitest --marionette localhost:$(($(($RANDOM))+2000)) $MOCHITEST_PARAMS $TEST_PARAMS 2>&1 | tee $TEST_DIR/mochitest$TEST_FLAVOUR
  #fi

  # WebRender testing
  export TEST_PARAMS="--enable-webrender $TEST_PARAMS"
  export TEST_FLAVOUR="-wr"
  # Use dom/base/test or dom/base/test/chrome for short version
  export MOCHITEST_DIR='dom'
  if [ $RUN_REFTEST -ne 0 ] ; then
    ./mach reftest $TEST_PARAMS 2>&1 | tee $TEST_DIR/reftest$TEST_FLAVOUR
    sleep 60
  fi
  if [ $RUN_CRASHTEST -ne 0 ] ; then
    ./mach crashtest $TEST_PARAMS 2>&1 | tee $TEST_DIR/crashtest$TEST_FLAVOUR
    sleep 60
  fi
  if [ $RUN_MOCHITEST -ne 0 ] ; then
    ./mach mochitest $MOCHITEST_DIR $MOCHITEST_PARAMS $TEST_PARAMS 2>&1 | tee $TEST_DIR/mochitest$TEST_FLAVOUR
    sleep 60
  fi

  rm -f  objdir/dist/bin/certutil
  rm -f  objdir/dist/bin/pk12util
}

function run_tests_x11() {
  set -x

  export MACH_USE_SYSTEM_PYTHON=1
  export MOZ_NODE_PATH=/usr/bin/node
  export X_PARAMS="-screen 0 1600x1200x24"
  export MOCHITEST_PARAMS="--timeout 1 --chunk-by-dir 4"
  export TEST_DIR="test_results"

  # Fix for system nss
  ln -s /usr/bin/certutil objdir/dist/bin/certutil
  ln -s /usr/bin/pk12util objdir/dist/bin/pk12util

  NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"

  # Basic render testing
  export TEST_PARAMS=""
  export TEST_FLAVOUR=""
  #xvfb-run -s "$X_PARAMS" -n 91 ./mach xpcshell-test --sequential $TEST_PARAMS 2>&1 | cat - | tee $TEST_DIR/xpcshell
  #xvfb-run -s "$X_PARAMS" -n 92 ./mach reftest --marionette localhost:$(($(($RANDOM))+2000)) $TEST_PARAMS 2>&1 | tee $TEST_DIR/reftest$TEST_FLAVOUR
  #xvfb-run -s "$X_PARAMS" -n 93 ./mach crashtest --marionette localhost:$(($(($RANDOM))+2000)) $TEST_PARAMS 2>&1 | tee $TEST_DIR/crashtest$TEST_FLAVOUR
  #xvfb-run -s "$X_PARAMS" -n 94 ./mach mochitest --marionette localhost:$(($(($RANDOM))+2000)) $MOCHITEST_PARAMS $TEST_PARAMS 2>&1 | tee $TEST_DIR/mochitest$TEST_FLAVOUR

  # WebRender testing
  export TEST_PARAMS="--enable-webrender $TEST_PARAMS"
  export TEST_FLAVOUR="-wr"
  #xvfb-run -s "$X_PARAMS" -n 95 ./mach xpcshell-test --sequential $TEST_PARAMS 2>&1 | cat - | tee $TEST_DIR/xpcshell-wr
  #sleep 60
  #xvfb-run -s "$X_PARAMS" -n 96 ./mach reftest $TEST_PARAMS 2>&1 | tee $TEST_DIR/reftest$TEST_FLAVOUR
  #sleep 60
  #xvfb-run -s "$X_PARAMS" -n 97 ./mach crashtest $TEST_PARAMS 2>&1 | tee $TEST_DIR/crashtest$TEST_FLAVOUR
  #sleep 60
  #export DISPLAY=:0
  #./mach mochitest dom/base/test/ $MOCHITEST_PARAMS $TEST_PARAMS 2>&1 | tee $TEST_DIR/mochitest$TEST_FLAVOUR
  export DISPLAY=:98
  xvfb-run -s "$X_PARAMS" -n 98 ./mach mochitest dom/base/test/ $MOCHITEST_PARAMS $TEST_PARAMS 2>&1 | tee $TEST_DIR/mochitest$TEST_FLAVOUR

  rm -f  objdir/dist/bin/certutil
  rm -f  objdir/dist/bin/pk12util
}

function run_wayland_compositor() {
  # Run wayland compositor and set WAYLAND_DISPLAY env variable
  set -x

  echo export DESKTOP_SESSION=gnome > $HOME/.xsessionrc
  echo export XDG_CURRENT_DESKTOP=GNOME > $HOME/.xsessionrc
  echo export XDG_SESSION_TYPE=wayland >> $HOME/.xsessionrc

  # Turn off the screen saver and screen locking
  gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
  gsettings set org.gnome.desktop.screensaver lock-enabled false
  gsettings set org.gnome.desktop.screensaver lock-delay 3600

  # Disable the screen saver
  # This starts the gnome-keyring-daemon with an unlocked login keyring. libsecret uses this to
  # store secrets. Firefox uses libsecret to store a key that protects sensitive information like
  # credit card numbers.
  if test -z "$DBUS_SESSION_BUS_ADDRESS" ; then
      # if not found, launch a new one
      eval `dbus-launch --sh-syntax`
  fi
  eval `echo '' | /usr/bin/gnome-keyring-daemon -r -d --unlock --components=secrets`

  if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR=$HOME
  fi

  . xvfb-run -s "-screen 0 1600x1200x24" -n 80 mutter --display=:80 --wayland --nested &
  export DISPLAY=:80

  if [ -z "$WAYLAND_DISPLAY" ] ; then
    export WAYLAND_DISPLAY=wayland-0
  else
    export WAYLAND_DISPLAY=wayland-1
  fi
  sleep 10
  retry_count=0
  max_retries=5
  until [ $retry_count -gt $max_retries ]; do
    if [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
      retry_count=$(($max_retries + 1))
    else
      retry_count=$(($retry_count + 1))
      echo "Waiting for Mutter, retry: $retry_count"
      sleep 2
    fi
  done

  env | grep "DISPLAY"
}

function print_error_reftest() {
  # Print reftest failures and compose them to html

  TEST_DIR="$1"
  TEST_FLAVOUR="$2"
  OUTPUT_FILE="failures-reftest$TEST_FLAVOUR.html"

  grep --text -e "REFTEST TEST-UNEXPECTED-PASS" -e "REFTEST TEST-UNEXPECTED-FAIL" -e "IMAGE 1 (TEST):" -e "IMAGE 2 (REFERENCE):" $TEST_DIR/reftest$TEST_FLAVOUR 2>&1 > $OUTPUT_FILE
  sed -i '/REFTEST   IMAGE 1/a ">' $OUTPUT_FILE
  sed -i '/REFTEST   IMAGE 2/a "><BR><BR>' $OUTPUT_FILE
  sed -i '/REFTEST TEST/a <BR>' $OUTPUT_FILE
  sed -i -e 's/^REFTEST   IMAGE 1 (TEST): /<img border=2 src="/' $OUTPUT_FILE
  sed -i -e 's/^REFTEST   IMAGE 2 (REFERENCE): /<img border=2 src="/' $OUTPUT_FILE
}

function print_errors() {
  #!/usr/bin/bash
  # Print failed tests

  TEST_DIR=$1
  TEST_FLAVOUR=$2

  grep "TEST-UNEXPECTED-FAIL" $TEST_DIR/mochitest$TEST_FLAVOUR 2>&1 > failures-mochitest$TEST_FLAVOUR.txt
  grep --text -e "  FAIL " -e "  TIMEOUT " $TEST_DIR/xpcshell$TEST_FLAVOUR 2>&1 > failures-xpcshell$TEST_FLAVOUR.txt
  grep --text -e "REFTEST TEST-UNEXPECTED-PASS" -e "REFTEST TEST-UNEXPECTED-FAIL" $TEST_DIR/reftest$TEST_FLAVOUR 2>&1 > failures-reftest$TEST_FLAVOUR.txt
}

function print_failures() {
  #!/usr/bin/bash
  # Analyze and print test failures

  export TEST_DIR="test_results"

  #./print-errors $TEST_DIR ""
  print_errors $TEST_DIR "-wr"
  #./print-error-reftest $TEST_DIR ""
  print_error_reftest $TEST_DIR "-wr"
}

function psummary() {
  #!/usr/bin/bash
  # Analyze and print specialized (basic/webrender) test results

  TEST_DIR=$1
  TEST_FLAVOUR=$2

  MPASS=`grep "TEST_END: Test OK" $TEST_DIR/mochitest$TEST_FLAVOUR | wc -l`
  MERR=`grep "TEST_END: Test ERROR" $TEST_DIR/mochitest$TEST_FLAVOUR | wc -l`
  MUNEX=`grep "TEST-UNEXPECTED-FAIL" $TEST_DIR/mochitest$TEST_FLAVOUR | wc  -l`
  echo "Mochitest   PASSED: $MPASS FAILED: $MERR UNEXPECTED-FAILURES: $MUNEX"

  XPCPASS=`grep --text "Expected results:" $TEST_DIR/xpcshell$TEST_FLAVOUR | cut -d ' ' -f 3`
  XPCFAIL=`grep --text "Unexpected results:" $TEST_DIR/xpcshell$TEST_FLAVOUR | cut -d ' ' -f 3`
  echo "XPCShell:   PASSED: $XPCPASS FAILED: $XPCFAIL"

  CRPASS=`grep "REFTEST INFO | Successful:" $TEST_DIR/crashtest$TEST_FLAVOUR | cut -d ' ' -f 5`
  CRFAIL=`grep "^REFTEST INFO | Unexpected:" $TEST_DIR/crashtest$TEST_FLAVOUR | cut -d ' ' -f 5`
  echo "Crashtest:  PASSED: $CRPASS FAILED: $CRFAIL"

  RFPASS=`grep --text "REFTEST INFO | Successful:" $TEST_DIR/reftest$TEST_FLAVOUR | cut -d ' ' -f 5`
  RFUN=`grep --text "^REFTEST INFO | Unexpected:" $TEST_DIR/reftest$TEST_FLAVOUR | cut -d ' ' -f 5`
  RFKNOWN=`grep --text "REFTEST INFO | Known problems:" $TEST_DIR/reftest$TEST_FLAVOUR | cut -d ' ' -f 6`
  echo "Reftest:    PASSED: $RFPASS FAILED: $RFUN Known issues: $RFKNOWN"
}

function print_results() {
  #!/usr/bin/bash
  # Analyze and print general test results

  export TEST_DIR="test_results"

  echo "Test results"
  #echo "Basic compositor"
  #./psummary $TEST_DIR ""
  echo "WebRender"
  psummary $TEST_DIR "-wr"
}

set -x
first=$1
shift
$first $*

