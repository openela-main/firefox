%define homepage %(grep '^HOME_URL\s*=' /etc/os-release | sed 's/^HOME_URL\s*=//;s/^\s*"//;s/"\s*$//')
%global disable_toolsets  0

# Produce debug (non-optimized) package build. Suitable for debugging only
# as the build is *very* slow.
%global debug_build       0
# Run Mozilla test suite as a part of compile rpm section. Turn off when
# building locally and don't want to spend 24 hours waiting for results.
%global run_firefox_tests 0

%ifarch x86_64 %{ix86}
%global run_firefox_tests 0
%endif

%ifarch x86_64
%if 0%{?rhel} == 7
# Disable debuginfo package and strip all binaries to avoid 4GB cpio limit
%define _binary_payload w19T16.xzdio
%global debug_package %{nil}
%define _enable_debug_packages 0
%define __spec_install_post \
    %{__arch_install_post} \
    %{__os_install_post} \
    find %{buildroot}%{mozappdir} -type f -name "*.so" -exec eu-strip --strip-debug {} \\; 2>/dev/null || find %{buildroot}%{mozappdir} -type f -name "*.so" -exec strip --strip-debug {} \\; \
    eu-strip --strip-all %{buildroot}%{mozappdir}/firefox-bin 2>/dev/null || strip --strip-all %{buildroot}%{mozappdir}/firefox-bin || : \
    eu-strip --strip-all %{buildroot}%{mozappdir}/firefox 2>/dev/null || strip --strip-all %{buildroot}%{mozappdir}/firefox || : \
    eu-strip --strip-all %{buildroot}%{mozappdir}/plugin-container 2>/dev/null || strip --strip-all %{buildroot}%{mozappdir}/plugin-container || :
%endif
%endif

# wasi_sdk is for sandboxing third party c/c++ libs by using rlbox, exclude s390x on the f39.

%global with_wasi_sdk 0

%{lua:
function dist_to_rhel_minor(str, start)
  match = string.match(str, ".module%+el8.%d+")
  if match then
     return string.sub(match, 13)
  end
  match = string.match(str, ".el8_%d+")
  if match then
     return string.sub(match, 6)
  end
  match = string.match(str, ".el8")
  if match then
     return 10
  end
  match = string.match(str, ".module%+el9.%d+")
  if match then
     return string.sub(match, 13)
  end
  match = string.match(str, ".el9_%d+")
  if match then
     return string.sub(match, 6)
  end
  match = string.match(str, ".el9")
  if match then
     return 7
  end
  match = string.match(str, ".el10_%d+")
  if match then
     return string.sub(match, 7)
  end
  match = string.match(str, ".el10")
  if match then
     return 1
  end
  return -1
end}

%global rhel_minor_version %{lua:print(dist_to_rhel_minor(rpm.expand("%dist")))}

%if 0%{?rhel} == 10
%global use_pipewire_camera 1
%else
%global use_pipewire_camera 0
%endif

# System libraries options
%global system_nss        1
%global bundle_nss        0

%if 0%{?rhel} == 7
  %global bundle_nss               0
  %global system_nss               0
%endif

%if 0%{?rhel} == 8
  %if %{rhel_minor_version} <= 8
    %global bundle_nss        1
    %global system_nss        1
  %endif
  %if %{rhel_minor_version} >= 10
    %ifnarch s390x
      %global with_wasi_sdk 1
    %endif
  %endif
%endif

%if 0%{?rhel} == 9
  %if %{rhel_minor_version} < 6
    %global bundle_nss        1
    %global system_nss        1
  %endif
  %if %{rhel_minor_version} > 5
    %ifnarch s390x
      %global with_wasi_sdk 1
    %endif
  %endif
%endif


%global dts_version       11
%global llvm_version      7.0
%global nspr_version      4.36
%global nspr_version_max  4.37
%global nss_version       3.112
%global nss_version_max   3.113
%global rust_version      1.84
%global system_libvpx     0
%if 0%{?rhel} >= 9 && %{rhel_minor_version} > 5
%global system_drm        1
%global system_gbm        1
%global system_pipewire   1
%else
%global system_drm        0
%global system_gbm        0
%global system_pipewire   0
%endif
# Workaround for missing httpd24 libs in rust
%if 0%{?rhel} == 7
%global ___build_pre %{___build_pre}; source scl_source enable httpd24 || :
%endif

# Toolsets setup
%global use_dts           0
%global use_gcc_ts        0
%global use_nodejs_scl    0
%global use_python3_scl   0

%global nodejs_build_req  nodejs

%if 0%{?rhel} > 7 && 0%{?rhel} < 10
  %global use_gcc_ts      1
  %if 0%{?rhel} == 9 && %{rhel_minor_version} >= 6
    # clang depends on gcc-toolset-14-gcc-c++
    %global gts_version 14
  %else
    %global gts_version 14
  %endif
%endif

%if 0%{?rhel} == 7
  %global use_dts          1
  %global use_nodejs_scl   1
  %global nodejs_build_req rh-nodejs10-nodejs
  %global llvm_version     11.0
  %global use_python3_scl  1
%endif

%if 0%{?disable_toolsets}
%global use_dts           0
%global use_nodejs_scl    0
%global use_python3_scl   0
%endif

%global launch_wayland_compositor 0
%if 0%{?run_firefox_tests}
  %global test_on_wayland           1
  %global launch_wayland_compositor 1
  %global build_tests               1
%endif


%global mozappdir            %{_libdir}/firefox
%global langpackdir          %{mozappdir}/browser/extensions
%define bundled_install_path %{mozappdir}/bundled
%global pre_version          esr
# Workaround the dreaded "upstream source file changed content" rpminspect failure.
# If set to .b2 or .b3 ... the processed source file needs to be renamed before upload, e.g.
# firefox-102.8.0esr.b2.processed-source.tar.xz
# When unset use processed source file name as is.
#%%global buildnum .b2

%bcond_without langpacks

# Exclude private libraries from autogenerated provides and requires
%global __provides_exclude_from ^%{mozappdir}
%global __requires_exclude ^(%%(find %{buildroot}%{mozappdir} -name '*.so' | xargs -n1 basename | sort -u | paste -s -d '|' -))

Summary:        Mozilla Firefox Web browser
Name:           firefox
Version:        140.5.0
Release:        2%{?dist}
URL:            https://www.mozilla.org/firefox/
License:        MPLv1.1 or GPLv2+ or LGPLv2+

%if 0%{?rhel} >= 9
ExcludeArch:    %{ix86}
%endif
%if 0%{?rhel} == 8
  # Started to ship on aarch64 in RHEL 8.2, on s390x in RHEL 8.3
  %if %{rhel_minor_version} == 1
ExcludeArch:    %{ix86} s390x aarch64
  %else
    %if %{rhel_minor_version} == 2
ExcludeArch:    %{ix86} s390x
    %else
ExcludeArch:    %{ix86}
    %endif
  %endif
%endif
%if 0%{?rhel} == 7
ExcludeArch:    aarch64 s390 ppc
%endif

# We can't use the official tarball as it contains some test files that use
# licenses that are rejected by Red Hat Legal.
# The official tarball has to be always processed by the process-official-tarball
# script
# Link to original tarball: https://archive.mozilla.org/pub/firefox/releases/%%{version}%%{?pre_version}/source/firefox-%%{version}%%{?pre_version}.source.tar.xz
Source0:        firefox-%{version}%{?pre_version}%{?buildnum}.processed-source.tar.xz
%if %{with langpacks}
Source1:        firefox-langpacks-%{version}%{?pre_version}-20251107.tar.xz
%endif
Source2:        cbindgen-vendor.tar.xz
Source3:        process-official-tarball
Source10:       firefox-mozconfig
Source12:       firefox-redhat-default-prefs.js
Source20:       firefox.desktop
Source21:       firefox.sh.in
Source23:       firefox.1
Source24:       mozilla-api-key
Source25:       firefox-symbolic.svg
Source26:       distribution.ini.in
Source27:       google-api-key
Source30:       firefox-x11.sh.in
Source31:       firefox-x11.desktop
Source32:       node-stdout-nonblocking-wrapper
Source33:       firefox.appdata.xml.in
Source34:       firefox-search-provider.ini
Source35:       google-loc-api-key
Source36:       testing.sh
Source37:       mochitest-python.tar.gz
Source38:       wasi.patch.template
# Created by:
# git clone --recursive https://github.com/WebAssembly/wasi-sdk.git
# cd wasi-sdk && git-archive-all --force-submodules wasi-sdk-20.tar.gz
Source50:       wasi-sdk-20.tar.gz

# Bundled libraries
Source401:      nss-setup-flags-env.inc
Source402:      nspr-4.36.0-2.el8_2.src.rpm
Source403:      nss-3.112.0-4.el8_2.src.rpm
Source404:      nss-3.112.0-1.el9_4.src.rpm

# ---- RHEL specific patches ---
# -- Downstream only --
Patch01:        build-disable-elfhack.patch
Patch02:        firefox-gcc-build.patch
Patch03:        build-big-endian-errors.patch
Patch04:        build-rhel7-lower-node-min-version.patch
Patch05:        build-ppc64-abiv2.patch
Patch06:        build-rhel7-nasm-dwarf.patch
# Disable PipeWire support for PipeWire 0.2
Patch08:        rhbz-2131158-webrtc-nss-fix.patch
Patch09:        build-ffvpx.patch
Patch10:        build-disable-gamepad.patch
Patch11:        rhbz-71999-fips-youtube.patch
Patch13:        firefox-fix-build-with-system-pipewire.patch
Patch14:        build-system-nss.patch

# -- Upstreamed patches --
Patch51:        mozilla-bmo1170092.patch
Patch52:        exceptionHandled-for-IO-error-processhandler.patch
Patch53:        D245908.clear-lang-bundles.diff
Patch54:        D249071.restoreWinState.diff
# Removed Crash Annotation GraphicsCriticalError 
Patch55:        D266159.1760530435.diff

# -- Submitted upstream, not merged --
Patch101:       mozilla-bmo1636168-fscreen.patch
Patch102:       mozilla-bmo1670333.patch
# Big endian fix
Patch103:       mozilla-bmo1504834-part1.patch
Patch104:       mozilla-bmo1504834-part3.patch
# Big endian fix
Patch105:       mozilla-bmo849632.patch
# Big endian fix
Patch106:       mozilla-bmo998749.patch
# Big endian fix
Patch107:       mozilla-bmo1716707-swizzle.patch
Patch108:       mozilla-bmo1716707-svg.patch
Patch109:       mozilla-bmo1789216-disable-av1.patch
Patch110:       build-libaom.patch
Patch111:       av1-else-condition-add.patch

# ML-DSA support
# https://phabricator.services.mozilla.com/D262395
Patch120:       firefox-integrate-ml-dsa-signature-verification-for-pkix-certificate-chain-validation.patch
# https://phabricator.services.mozilla.com/D262397
Patch121:       firefox-add-ml-dsa-certificate-support-to-certviewer.patch
# https://phabricator.services.mozilla.com/D264144
Patch122:       firefox-enable-ml-dsa-signature-verification-for-certificate-chain-validation.patch
# RHEL downstream only - adapts to ML-DSA support in NSS from RHEL 10
Patch123:       firefox-adapt-ml-dsa-support-to-rhel-nss.patch
# RHEL downstream only - enable ML-DSA in manager/ssl
Patch124:       firefox-enable-ml-dsa-in-manager-ssl.patch
# RHEL downstream only - add mlkem768-secp256r1 support
Patch125:       firefox-add-mlkem768-secp256r1-support.patch

# ---- Fedora specific patches ----
Patch151:       firefox-enable-addons.patch
Patch152:       rhbz-1173156.patch
Patch153:       firefox-nss-addon-hack.patch

# ARM run-time patch
Patch154:       rhbz-1354671.patch

# --- fips webrtc fix
Patch200:       webrtc-128.0.patch
Patch201:       D224587.1728128070.diff
Patch202:       D224588.1728128098.diff
Patch203:       wasi.patch

# ---- Test patches ----
# Generate without context by
# GENDIFF_DIFF_ARGS=-U0 gendiff firefox-xxxx .firefox-tests-xpcshell
# GENDIFF_DIFF_ARGS=-U0 gendiff firefox-xxxx .firefox-tests-reftest

# ---- Security patches ----

# BUILD REQURES/REQUIRES
%if %{?system_nss} && !0%{?bundle_nss}
BuildRequires:  pkgconfig(nspr) >= %{nspr_version}
BuildRequires:  pkgconfig(nspr) < %{nspr_version_max}
BuildRequires:  pkgconfig(nss) >= %{nss_version}
BuildRequires:  pkgconfig(nss) < %{nss_version_max}
BuildRequires:  nss-static >= %{nss_version}
BuildRequires:  nss-static < %{nss_version_max}
%endif

%if %{?system_libvpx}
BuildRequires:  libvpx-devel >= 1.8.2
%endif

%if 0%{?rhel} == 7
BuildRequires:	devtoolset-11-elfutils
%endif
BuildRequires:  bzip2-devel
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  libjpeg-devel
BuildRequires:  libstdc++-devel
BuildRequires:  libstdc++-static
BuildRequires:  m4
BuildRequires:  make
BuildRequires:  nasm >= 1.13
BuildRequires:  %{nodejs_build_req} >= 10.21
BuildRequires:  pciutils-libs
BuildRequires:  perl-interpreter
BuildRequires:  pkgconfig(alsa)
BuildRequires:  pkgconfig(dri)
BuildRequires:  pkgconfig(freetype2)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(krb5)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  pkgconfig(libffi)
BuildRequires:  pkgconfig(libnotify)
BuildRequires:  pkgconfig(libpng)
BuildRequires:  pkgconfig(libpulse)
BuildRequires:  pkgconfig(libstartup-notification-1.0)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(xrender)
BuildRequires:  pkgconfig(xt)
BuildRequires:  pkgconfig(xtst)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  zip

%if 0%{?rhel} == 7
%if 0%{?use_python3_scl}
BuildRequires:  rh-python38-python-devel
BuildRequires:  rh-python38-python-setuptools
BuildRequires:  scl-utils
%endif
BuildRequires:  findutils
%else
BuildRequires:  pipewire-devel
%endif

%if 0%{?rhel} == 8
BuildRequires:  cargo
BuildRequires:  clang-libs >= %{llvm_version}
BuildRequires:  clang-devel >= %{llvm_version}
BuildRequires:  clang >= %{llvm_version}
BuildRequires:  llvm-devel >= %{llvm_version}
BuildRequires:  llvm >= %{llvm_version}
  %if 0%{?disable_toolsets} == 0
BuildRequires:  python38-devel
BuildRequires:  python38-setuptools
  %endif
BuildRequires:  rustfmt >= %{rust_version}
BuildRequires:  rust >= %{rust_version}
%endif

%if 0%{?rhel} >= 9
BuildRequires:  cargo
BuildRequires:  clang clang-libs llvm llvm-devel
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  rust
%endif

%if 0%{?rhel} == 7
BuildRequires:  cargo
BuildRequires:  clang clang-libs llvm llvm-devel
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  rust
%ifnarch ppc64
BuildRequires:  httpd24-curl
%endif
%endif

%if 0%{?use_dts}
BuildRequires:  devtoolset-%{dts_version}-gcc
BuildRequires:  devtoolset-%{dts_version}-gcc-c++
BuildRequires:  devtoolset-%{dts_version}-libatomic-devel
%endif

# Bundled nss/nspr requirement
%if 0%{?bundle_nss}
BuildRequires:    gawk
BuildRequires:    gcc-c++
BuildRequires:    nss-softokn
BuildRequires:    perl-interpreter
BuildRequires:    pkgconfig
BuildRequires:    psmisc
BuildRequires:    sqlite-devel
BuildRequires:    xmlto
BuildRequires:    zlib-devel
%endif

%if %{with_wasi_sdk}
BuildRequires:  lld
BuildRequires:  clang cmake ninja-build
%endif

%if %{?system_drm}
BuildRequires:  libdrm-devel
%endif

%if %{?system_gbm}
BuildRequires:  mesa-libgbm-devel
%endif

%if %{?system_pipewire}
BuildRequires:  pipewire-devel
%endif

%if !0%{?flatpak}
#TODO
BuildRequires:  system-bookmarks
%endif

%if 0%{?test_on_wayland}
BuildRequires:  dbus-x11
BuildRequires:  gnome-keyring
BuildRequires:  gnome-settings-daemon
BuildRequires:  gsettings-desktop-schemas
BuildRequires:  mesa-dri-drivers
BuildRequires:  mutter
BuildRequires:  xorg-x11-server-Xwayland
%endif

%if 0%{?run_firefox_tests}
BuildRequires:  abattis-cantarell-fonts
BuildRequires:  dbus-x11
BuildRequires:  dejavu-sans-fonts
BuildRequires:  dejavu-sans-mono-fonts
BuildRequires:  dejavu-serif-fonts
BuildRequires:  gnome-keyring
BuildRequires:  google-carlito-fonts
BuildRequires:  google-droid-sans-fonts
BuildRequires:  google-noto-cjk-fonts-common
BuildRequires:  google-noto-emoji-color-fonts
BuildRequires:  google-noto-fonts-common
BuildRequires:  google-noto-sans-cjk-ttc-fonts
BuildRequires:  google-noto-sans-fonts
BuildRequires:  google-noto-sans-gurmukhi-fonts
BuildRequires:  google-noto-sans-sinhala-vf-fonts
BuildRequires:  jomolhari-fonts
BuildRequires:  khmeros-base-fonts
BuildRequires:  liberation-fonts-common
BuildRequires:  liberation-mono-fonts
BuildRequires:  liberation-sans-fonts
BuildRequires:  liberation-serif-fonts
BuildRequires:  lohit-tamil-fonts
BuildRequires:  lohit-telugu-fonts
BuildRequires:  mesa-dri-drivers
BuildRequires:  nss-tools
BuildRequires:  paktype-naskh-basic-fonts
BuildRequires:  procps-ng
BuildRequires:  pt-sans-fonts
#BuildRequires:  smc-meera-fonts
BuildRequires:  stix-fonts
BuildRequires:  thai-scalable-fonts-common
BuildRequires:  thai-scalable-waree-fonts
BuildRequires:  xorg-x11-fonts-ISO8859-1-100dpi
BuildRequires:  xorg-x11-fonts-misc
BuildRequires:  xorg-x11-server-Xvfb
%endif

%if 0%{?use_gcc_ts}
BuildRequires: gcc-toolset-%{gts_version}-runtime
BuildRequires: gcc-toolset-%{gts_version}-binutils
BuildRequires: gcc-toolset-%{gts_version}-gcc
BuildRequires: gcc-toolset-%{gts_version}-gcc-plugin-annobin
# Do not explicitly require gcc-toolset-%{gts_version}-gcc-g++ instead fail
# when clang is upgraded to depend on a later toolset and adjust version.
%endif

Requires:       mozilla-filesystem
Requires:       p11-kit-trust
Requires:       pciutils-libs
Requires:       redhat-indexhtml

%if %{?system_nss} && !0%{?bundle_nss}
Requires:       nspr >= %{nspr_version}
Requires:       nss >= %{nss_version}
%endif

Obsoletes:      mozilla <= 37:1.7.13
Provides:       webclient

# Bundled libraries
#Provides: bundled(libjxl) it's used only on nightly builds
Provides: bundled(abseil-cpp)
Provides: bundled(angle)
Provides: bundled(aom)
Provides: bundled(audioipc-2)
Provides: bundled(bergamot-translator)
Provides: bundled(brotli)
Provides: bundled(bsdiff)
Provides: bundled(bspatch)
Provides: bundled(cairo)
Provides: bundled(cfworker)
Provides: bundled(cld2)
Provides: bundled(content)
Provides: bundled(content_analysis_sdk)
Provides: bundled(cts)
Provides: bundled(cubeb)
Provides: bundled(d3)
Provides: bundled(dav1d)
Provides: bundled(double-conversion)
Provides: bundled(drm)
Provides: bundled(expat)
Provides: bundled(fathom)
Provides: bundled(fdlibm)
Provides: bundled(ffvpx)
Provides: bundled(fmt)
Provides: bundled(function2)
Provides: bundled(gbm)
Provides: bundled(gemmology)
Provides: bundled(googletest)
Provides: bundled(graphite2)
Provides: bundled(harfbuzz)
Provides: bundled(highway)
Provides: bundled(hunspell)
Provides: bundled(intgemm)
Provides: bundled(irregexp)
Provides: bundled(java)
Provides: bundled(jpeg-xl)
Provides: bundled(js)
Provides: bundled(libaom)
Provides: bundled(libcubeb)
Provides: bundled(libdav1d)
Provides: bundled(libdrm)
Provides: bundled(libepoxy)
Provides: bundled(libfuzzer)
Provides: bundled(libgbm)
Provides: bundled(libjpeg)
Provides: bundled(libjxl)
Provides: bundled(libmar)
Provides: bundled(libmkv)
Provides: bundled(libnestegg)
Provides: bundled(libogg)
Provides: bundled(libopus)
Provides: bundled(libpng)
Provides: bundled(libsoundtouch)
Provides: bundled(libspeex_resampler)
Provides: bundled(libsrtp)
Provides: bundled(libvorbis)
Provides: bundled(libvpx)
Provides: bundled(libwebp)
Provides: bundled(libwebrtc)
Provides: bundled(libyuv)
Provides: bundled(lit)
Provides: bundled(MotionMark)
Provides: bundled(mp4parse-rust)
Provides: bundled(msgpack)
Provides: bundled(nICEr)
Provides: bundled(nss)
Provides: bundled(opentelemetry-cpp)
Provides: bundled(openmax_il)
Provides: bundled(openvr)
Provides: bundled(ots)
Provides: bundled(pdf.js)
Provides: bundled(pdfjs)
Provides: bundled(perfetto)
Provides: bundled(picosha2)
Provides: bundled(pipewire)
Provides: bundled(PKI.js)
Provides: bundled(puppeteer)
Provides: bundled(python)
Provides: bundled(pywebsocket3)
Provides: bundled(qcms)
Provides: bundled(reader)
Provides: bundled(rlbox)
Provides: bundled(rlbox_wasm2c_sandbox)
Provides: bundled(schemas)
Provides: bundled(simde)
Provides: bundled(sipcc)
Provides: bundled(skia)
Provides: bundled(source-map)
Provides: bundled(Speedometer3)
Provides: bundled(sqlite3)
Provides: bundled(sqlite-vec)
Provides: bundled(src)
Provides: bundled(transformers)
Provides: bundled(thebes)
Provides: bundled(vendor)
Provides: bundled(vsdownload)
Provides: bundled(wasm2c)
Provides: bundled(wasm2c_sandbox_compiler)
Provides: bundled(wayland-proxy)
Provides: bundled(webaudio)
Provides: bundled(webgl-conf)
Provides: bundled(WebRender)
Provides: bundled(wgpu_bindings)
Provides: bundled(widevine-adapter)
Provides: bundled(wllama)
Provides: bundled(woff2)
Provides: bundled(xsimd)
Provides: bundled(xz-embedded)
Provides: bundled(ycbcr)
Provides: bundled(zstd)
Provides: bundled(Zycore)
Provides: bundled(Zydis)

%if 0%{?bundle_nss}
Provides: bundled(nss) = %{nss_version}
Provides: bundled(nspr) = %{nspr_version}
%endif

# Rust third parties:
# List obtained by `get_rust_bundled_provides.sh build.log` script::
Provides: bundled(crate(aa-stroke)) = 0.1.0
Provides: bundled(crate(adler)) = 1.0.2
Provides: bundled(crate(aho-corasick)) = 1.1.0
Provides: bundled(crate(allocator-api2)) = 0.2.999
Provides: bundled(crate(alsa)) = 0.8.1
Provides: bundled(crate(alsa-sys)) = 0.3.1
Provides: bundled(crate(anstream)) = 0.6.19
Provides: bundled(crate(anstyle)) = 1.0.11
Provides: bundled(crate(anstyle-parse)) = 0.2.7
Provides: bundled(crate(anstyle-query)) = 1.1.3
Provides: bundled(crate(anyhow)) = 1.0.69
Provides: bundled(crate(app_services_logger)) = 0.1.0
Provides: bundled(crate(app_units)) = 0.7.8
Provides: bundled(crate(arrayref)) = 0.3.6
Provides: bundled(crate(arraystring)) = 0.3.0
Provides: bundled(crate(arrayvec)) = 0.7.6
Provides: bundled(crate(ash)) = 0.38.0+1.3.281
Provides: bundled(crate(askama)) = 0.13.1
Provides: bundled(crate(askama_derive)) = 0.13.1
Provides: bundled(crate(askama_parser)) = 0.13.0
Provides: bundled(crate(async-task)) = 4.3.0
Provides: bundled(crate(async-trait)) = 0.1.68
Provides: bundled(crate(atomic_refcell)) = 0.1.9
Provides: bundled(crate(audioipc2)) = 0.6.0
Provides: bundled(crate(audioipc2-client)) = 0.6.0
Provides: bundled(crate(audioipc2-server)) = 0.6.0
Provides: bundled(crate(audio_thread_priority)) = 0.32.0
Provides: bundled(crate(authenticator)) = 0.4.1
Provides: bundled(crate(authrs_bridge)) = 0.1.0
Provides: bundled(crate(autocfg)) = 1.1.0
Provides: bundled(crate(base64)) = 0.21.999
Provides: bundled(crate(base64)) = 0.22.1
Provides: bundled(crate(basic-toml)) = 0.1.2
Provides: bundled(crate(bhttp)) = 0.3.1
Provides: bundled(crate(binary_http)) = 0.1.0
Provides: bundled(crate(bincode)) = 1.3.3
Provides: bundled(crate(bindgen)) = 0.64.999
Provides: bundled(crate(bindgen)) = 0.69.4
Provides: bundled(crate(bitflags)) = 1.3.2
Provides: bundled(crate(bitflags)) = 1.999.999
Provides: bundled(crate(bitflags)) = 2.9.0
Provides: bundled(crate(bitreader)) = 0.3.6
Provides: bundled(crate(bit-set)) = 0.8.0
Provides: bundled(crate(bit-vec)) = 0.8.0
Provides: bundled(crate(block-buffer)) = 0.10.3
Provides: bundled(crate(bookmark_sync)) = 0.1.0
Provides: bundled(crate(buildid_reader)) = 0.1.0
Provides: bundled(crate(buildid_reader_ffi)) = 0.1.0
Provides: bundled(crate(build-parallel)) = 0.1.2
Provides: bundled(crate(bumpalo)) = 3.15.4
Provides: bundled(crate(bytemuck)) = 1.22.0
Provides: bundled(crate(bytemuck_derive)) = 1.9.3
Provides: bundled(crate(byteorder)) = 1.5.0
Provides: bundled(crate(bytes)) = 1.4.0
Provides: bundled(crate(cache-padded)) = 1.2.0
Provides: bundled(crate(calendrical_calculations)) = 0.1.1
Provides: bundled(crate(camino)) = 1.1.2
Provides: bundled(crate(cargo_metadata)) = 0.19.2
Provides: bundled(crate(cargo-platform)) = 0.1.2
Provides: bundled(crate(cascade_bloom_filter)) = 0.1.0
Provides: bundled(crate(cbindgen)) = 0.27.0
Provides: bundled(crate(cc)) = 1.2.12
Provides: bundled(crate(cert_storage)) = 0.0.1
Provides: bundled(crate(cexpr)) = 0.6.0
Provides: bundled(crate(cfg_aliases)) = 0.2.1
Provides: bundled(crate(cfg-if)) = 1.0.0
Provides: bundled(crate(chardetng)) = 0.1.9
Provides: bundled(crate(chardetng_c)) = 0.1.2
Provides: bundled(crate(chrono)) = 0.4.40
Provides: bundled(crate(chunky-vec)) = 0.1.0
Provides: bundled(crate(clang-sys)) = 1.7.0
Provides: bundled(crate(clap)) = 4.5.39
Provides: bundled(crate(clap_builder)) = 4.5.39
Provides: bundled(crate(clap_lex)) = 0.7.4
Provides: bundled(crate(clubcard)) = 0.3.2
Provides: bundled(crate(clubcard-crlite)) = 0.3.0
Provides: bundled(crate(cmake)) = 0.1.999
Provides: bundled(crate(codespan-reporting)) = 0.12.0
Provides: bundled(crate(colorchoice)) = 1.0.4
Provides: bundled(crate(context_id)) = 0.1.0
Provides: bundled(crate(core_maths)) = 0.1.0
Provides: bundled(crate(cose)) = 0.1.4
Provides: bundled(crate(cose-c)) = 0.1.5
Provides: bundled(crate(cpufeatures)) = 0.2.8
Provides: bundled(crate(crc32fast)) = 1.4.2
Provides: bundled(crate(crossbeam-channel)) = 0.5.13
Provides: bundled(crate(crossbeam-deque)) = 0.8.2
Provides: bundled(crate(crossbeam-epoch)) = 0.9.14
Provides: bundled(crate(crossbeam-queue)) = 0.3.8
Provides: bundled(crate(crossbeam-utils)) = 0.8.20
Provides: bundled(crate(crypto-common)) = 0.1.6
Provides: bundled(crate(crypto_hash)) = 0.1.0
Provides: bundled(crate(cssparser)) = 0.34.1
Provides: bundled(crate(cssparser-macros)) = 0.6.1
Provides: bundled(crate(cstr)) = 0.2.11
Provides: bundled(crate(cubeb)) = 0.13.0
Provides: bundled(crate(cubeb-backend)) = 0.13.0
Provides: bundled(crate(cubeb-core)) = 0.13.0
Provides: bundled(crate(cubeb-pulse)) = 0.5.0
Provides: bundled(crate(cubeb-sys)) = 0.13.0
Provides: bundled(crate(dap_ffi)) = 0.1.0
Provides: bundled(crate(darling)) = 0.20.10
Provides: bundled(crate(darling_core)) = 0.20.10
Provides: bundled(crate(darling_macro)) = 0.20.10
Provides: bundled(crate(data-encoding)) = 2.3.3
Provides: bundled(crate(data-encoding-ffi)) = 0.1.0
Provides: bundled(crate(data_storage)) = 0.0.1
Provides: bundled(crate(dbus)) = 0.6.5
Provides: bundled(crate(debug_tree)) = 0.4.0
Provides: bundled(crate(deranged)) = 0.3.11
Provides: bundled(crate(derive_more)) = 0.99.999
Provides: bundled(crate(derive_more)) = 1.0.0-beta.2
Provides: bundled(crate(derive_more-impl)) = 1.0.0-beta.2
Provides: bundled(crate(digest)) = 0.10.7
Provides: bundled(crate(diplomat)) = 0.8.0
Provides: bundled(crate(diplomat_core)) = 0.8.0
Provides: bundled(crate(diplomat-runtime)) = 0.8.0
Provides: bundled(crate(dirs)) = 4.0.0
Provides: bundled(crate(dirs-sys)) = 0.3.7
Provides: bundled(crate(displaydoc)) = 0.2.4
Provides: bundled(crate(dns-parser)) = 0.8.0
Provides: bundled(crate(document-features)) = 0.2.11
Provides: bundled(crate(dogear)) = 0.5.0
Provides: bundled(crate(dom)) = 0.1.0
Provides: bundled(crate(dom_fragmentdirectives)) = 0.1.0
Provides: bundled(crate(dtoa)) = 0.4.8
Provides: bundled(crate(dtoa-short)) = 0.3.3
Provides: bundled(crate(either)) = 1.8.1
Provides: bundled(crate(encoding_c)) = 0.9.8
Provides: bundled(crate(encoding_c_mem)) = 0.2.6
Provides: bundled(crate(encoding_glue)) = 0.1.0
Provides: bundled(crate(encoding_rs)) = 0.8.35
Provides: bundled(crate(enum-map)) = 2.7.3
Provides: bundled(crate(enum-map-derive)) = 0.17.0
Provides: bundled(crate(enumset)) = 1.1.2
Provides: bundled(crate(enumset_derive)) = 0.8.1
Provides: bundled(crate(env_logger)) = 0.10.0
Provides: bundled(crate(equivalent)) = 1.0.1
Provides: bundled(crate(equivalent)) = 1.0.2
Provides: bundled(crate(error-chain)) = 0.12.4
Provides: bundled(crate(error-support)) = 0.1.0
Provides: bundled(crate(error-support-macros)) = 0.1.0
Provides: bundled(crate(etagere)) = 0.2.13
Provides: bundled(crate(euclid)) = 0.22.10
Provides: bundled(crate(extend)) = 1.2.0
Provides: bundled(crate(fallible_collections)) = 0.4.9
Provides: bundled(crate(fallible-iterator)) = 0.3.0
Provides: bundled(crate(fallible-streaming-iterator)) = 0.1.9
Provides: bundled(crate(fastrand)) = 1.9.0
Provides: bundled(crate(fastrand)) = 2.1.1
Provides: bundled(crate(ffi-support)) = 0.4.4
Provides: bundled(crate(firefox-on-glean)) = 0.1.0
Provides: bundled(crate(firefox-versioning)) = 0.1.0
Provides: bundled(crate(flate2)) = 1.0.30
Provides: bundled(crate(fluent)) = 0.16.0
Provides: bundled(crate(fluent-bundle)) = 0.15.2
Provides: bundled(crate(fluent-fallback)) = 0.7.0
Provides: bundled(crate(fluent-ffi)) = 0.1.0
Provides: bundled(crate(fluent-langneg)) = 0.13.0
Provides: bundled(crate(fluent-langneg-ffi)) = 0.1.0
Provides: bundled(crate(fluent-pseudo)) = 0.3.1
Provides: bundled(crate(fluent-syntax)) = 0.11.0
Provides: bundled(crate(fnv)) = 1.0.7
Provides: bundled(crate(fog_control)) = 0.1.0
Provides: bundled(crate(foldhash)) = 0.1.5
Provides: bundled(crate(form_urlencoded)) = 1.2.1
Provides: bundled(crate(freetype)) = 0.7.0
Provides: bundled(crate(fs-err)) = 2.9.0
Provides: bundled(crate(futures)) = 0.3.28
Provides: bundled(crate(futures-channel)) = 0.3.28
Provides: bundled(crate(futures-core)) = 0.3.28
Provides: bundled(crate(futures-executor)) = 0.3.28
Provides: bundled(crate(futures-io)) = 0.3.28
Provides: bundled(crate(futures-macro)) = 0.3.28
Provides: bundled(crate(futures-sink)) = 0.3.28
Provides: bundled(crate(futures-task)) = 0.3.28
Provides: bundled(crate(futures-util)) = 0.3.28
Provides: bundled(crate(fxhash)) = 0.2.1
Provides: bundled(crate(gecko_logger)) = 0.1.0
Provides: bundled(crate(gecko-profiler)) = 0.1.0
Provides: bundled(crate(geckoservo)) = 0.0.1
Provides: bundled(crate(generic-array)) = 0.14.6
Provides: bundled(crate(getrandom)) = 0.2.999
Provides: bundled(crate(getrandom)) = 0.3.3
Provides: bundled(crate(gkrust)) = 0.1.0
Provides: bundled(crate(gkrust-shared)) = 0.1.0
Provides: bundled(crate(gkrust-uniffi-components)) = 0.1.0
Provides: bundled(crate(gkrust_utils)) = 0.1.0
Provides: bundled(crate(gleam)) = 0.15.0
Provides: bundled(crate(glean)) = 64.3.1
Provides: bundled(crate(glean-core)) = 64.3.1
Provides: bundled(crate(gl_generator)) = 0.14.0
Provides: bundled(crate(glob)) = 0.3.1
Provides: bundled(crate(glsl)) = 6.0.2
Provides: bundled(crate(glslopt)) = 0.1.11
Provides: bundled(crate(glsl-to-cxx)) = 0.1.0
Provides: bundled(crate(goblin)) = 0.8.999
Provides: bundled(crate(goblin)) = 0.9.2
Provides: bundled(crate(golden_gate)) = 0.1.0
Provides: bundled(crate(gpu-alloc)) = 0.6.0
Provides: bundled(crate(gpu-alloc-types)) = 0.3.0
Provides: bundled(crate(gpu-descriptor)) = 0.3.0
Provides: bundled(crate(gpu-descriptor-types)) = 0.2.0
Provides: bundled(crate(half)) = 1.999.999
Provides: bundled(crate(half)) = 2.5.0
Provides: bundled(crate(hashbrown)) = 0.13.999
Provides: bundled(crate(hashbrown)) = 0.14.999
Provides: bundled(crate(hashbrown)) = 0.15.2
Provides: bundled(crate(hashbrown)) = 0.15.3
Provides: bundled(crate(hashlink)) = 0.10.0
Provides: bundled(crate(heck)) = 0.4.1
Provides: bundled(crate(heck)) = 0.5.0
Provides: bundled(crate(hex)) = 0.4.3
Provides: bundled(crate(hexf-parse)) = 0.2.1
Provides: bundled(crate(http_sfv)) = 0.1.0
Provides: bundled(crate(iana-time-zone)) = 0.1.63
Provides: bundled(crate(icu_calendar)) = 1.5.2
Provides: bundled(crate(icu_calendar_data)) = 1.5.0
Provides: bundled(crate(icu_capi)) = 1.5.0
Provides: bundled(crate(icu_collections)) = 1.5.0
Provides: bundled(crate(icu_locid)) = 1.5.0
Provides: bundled(crate(icu_locid_transform)) = 1.5.0
Provides: bundled(crate(icu_locid_transform_data)) = 1.5.0
Provides: bundled(crate(icu_normalizer)) = 1.5.0
Provides: bundled(crate(icu_normalizer_data)) = 1.5.0
Provides: bundled(crate(icu_properties)) = 1.5.0
Provides: bundled(crate(icu_properties_data)) = 1.5.0
Provides: bundled(crate(icu_provider)) = 1.5.0
Provides: bundled(crate(icu_provider_adapters)) = 1.5.0
Provides: bundled(crate(icu_provider_macros)) = 1.5.0
Provides: bundled(crate(icu_segmenter)) = 1.5.0
Provides: bundled(crate(icu_segmenter_data)) = 1.5.0
Provides: bundled(crate(id-arena)) = 2.2.1
Provides: bundled(crate(ident_case)) = 1.0.1
Provides: bundled(crate(idna)) = 1.0.3
Provides: bundled(crate(idna_adapter)) = 1.2.0
Provides: bundled(crate(idna_glue)) = 0.1.0
Provides: bundled(crate(indexmap)) = 2.8.0
Provides: bundled(crate(indexmap)) = 2.9.0
Provides: bundled(crate(inherent)) = 1.0.7
Provides: bundled(crate(interrupt-support)) = 0.1.0
Provides: bundled(crate(intl-memoizer)) = 0.5.1
Provides: bundled(crate(intl_pluralrules)) = 7.0.2
Provides: bundled(crate(io-lifetimes)) = 1.0.10
Provides: bundled(crate(iovec)) = 0.1.4
Provides: bundled(crate(ipcclientcerts)) = 0.1.0
Provides: bundled(crate(ipdl_utils)) = 0.1.0
Provides: bundled(crate(is_terminal_polyfill)) = 1.70.1
Provides: bundled(crate(itertools)) = 0.10.999
Provides: bundled(crate(itertools)) = 0.14.0
Provides: bundled(crate(itoa)) = 1.0.15
Provides: bundled(crate(itoa)) = 1.0.6
Provides: bundled(crate(jexl-eval)) = 0.3.0
Provides: bundled(crate(jexl-parser)) = 0.3.0
Provides: bundled(crate(jobserver)) = 0.1.33
Provides: bundled(crate(jog)) = 0.1.0
Provides: bundled(crate(jsrust)) = 0.1.0
Provides: bundled(crate(jsrust_shared)) = 0.1.0
Provides: bundled(crate(keccak)) = 0.1.4
Provides: bundled(crate(khronos_api)) = 3.1.0
Provides: bundled(crate(kvstore)) = 0.1.0
Provides: bundled(crate(l10nregistry)) = 0.3.0
Provides: bundled(crate(l10nregistry-ffi)) = 0.1.0
Provides: bundled(crate(lalrpop-util)) = 0.19.12
Provides: bundled(crate(lazycell)) = 1.3.0
Provides: bundled(crate(lazy_static)) = 1.4.0
Provides: bundled(crate(leb128)) = 0.2.5
Provides: bundled(crate(libc)) = 0.2.144
Provides: bundled(crate(libc)) = 0.2.171
Provides: bundled(crate(libdbus-sys)) = 0.2.2
Provides: bundled(crate(libloading)) = 0.8.6
Provides: bundled(crate(libm)) = 0.2.6
Provides: bundled(crate(libsqlite3-sys)) = 0.31.0
Provides: bundled(crate(libudev)) = 0.2.0
Provides: bundled(crate(libudev-sys)) = 0.1.3
Provides: bundled(crate(linux-raw-sys)) = 0.3.7
Provides: bundled(crate(linux-raw-sys)) = 0.4.14
Provides: bundled(crate(litemap)) = 0.7.3
Provides: bundled(crate(litrs)) = 0.4.1
Provides: bundled(crate(lmdb-rkv-sys)) = 0.11.2
Provides: bundled(crate(localization-ffi)) = 0.1.0
Provides: bundled(crate(lock_api)) = 0.4.9
Provides: bundled(crate(log)) = 0.4.17
Provides: bundled(crate(log)) = 0.4.26
Provides: bundled(crate(malloc_size_of)) = 0.0.1
Provides: bundled(crate(malloc_size_of_derive)) = 0.1.3
Provides: bundled(crate(mapped_hyph)) = 0.4.3
Provides: bundled(crate(matches)) = 0.1.10
Provides: bundled(crate(maybe-async)) = 0.2.10
Provides: bundled(crate(md-5)) = 0.10.5
Provides: bundled(crate(mdns_service)) = 0.1.1
Provides: bundled(crate(memalloc)) = 0.1.0
Provides: bundled(crate(memchr)) = 2.7.4
Provides: bundled(crate(memmap2)) = 0.9.3
Provides: bundled(crate(memoffset)) = 0.8.999
Provides: bundled(crate(memoffset)) = 0.9.0
Provides: bundled(crate(midir)) = 0.7.0
Provides: bundled(crate(midir_impl)) = 0.1.0
Provides: bundled(crate(mime)) = 0.3.16
Provides: bundled(crate(mime_guess)) = 2.0.4
Provides: bundled(crate(mime-guess-ffi)) = 0.1.0
Provides: bundled(crate(minimal-lexical)) = 0.2.1
Provides: bundled(crate(miniz_oxide)) = 0.7.1
Provides: bundled(crate(mio)) = 1.0.1
Provides: bundled(crate(mls_gk)) = 0.1.0
Provides: bundled(crate(mls-platform-api)) = 0.1.0
Provides: bundled(crate(mls-rs)) = 0.45.0
Provides: bundled(crate(mls-rs-codec)) = 0.6.0
Provides: bundled(crate(mls-rs-codec-derive)) = 0.2.0
Provides: bundled(crate(mls-rs-core)) = 0.21.0
Provides: bundled(crate(mls-rs-crypto-hpke)) = 0.14.0
Provides: bundled(crate(mls-rs-crypto-nss)) = 0.1.0
Provides: bundled(crate(mls-rs-crypto-traits)) = 0.15.0
Provides: bundled(crate(mls-rs-identity-x509)) = 0.15.0
Provides: bundled(crate(mls-rs-provider-sqlite)) = 0.15.0
Provides: bundled(crate(moz_asserts)) = 0.1.0
Provides: bundled(crate(mozbuild)) = 0.1.0
Provides: bundled(crate(moz_cbor)) = 0.1.2
Provides: bundled(crate(mozglue-static)) = 0.1.0
Provides: bundled(crate(mozilla-central-workspace-hack)) = 0.1.0
Provides: bundled(crate(moz_task)) = 0.1.0
Provides: bundled(crate(mozurl)) = 0.0.1
Provides: bundled(crate(mp4parse)) = 0.17.0
Provides: bundled(crate(mp4parse_capi)) = 0.17.0
Provides: bundled(crate(mtu)) = 0.2.6
Provides: bundled(crate(murmurhash3)) = 0.0.5
Provides: bundled(crate(naga)) = 25.0.0
Provides: bundled(crate(neqo-common)) = 0.13.4
Provides: bundled(crate(neqo-crypto)) = 0.13.4
Provides: bundled(crate(neqo_glue)) = 0.1.0
Provides: bundled(crate(neqo-http3)) = 0.13.4
Provides: bundled(crate(neqo-qpack)) = 0.13.4
Provides: bundled(crate(neqo-transport)) = 0.13.4
Provides: bundled(crate(neqo-udp)) = 0.13.4
Provides: bundled(crate(netwerk_helper)) = 0.0.1
Provides: bundled(crate(new_debug_unreachable)) = 1.0.4
Provides: bundled(crate(nix)) = 0.26.99
Provides: bundled(crate(nix)) = 0.29.0
Provides: bundled(crate(nom)) = 7.1.3
Provides: bundled(crate(nserror)) = 0.1.0
Provides: bundled(crate(nss-gk-api)) = 0.3.0
Provides: bundled(crate(nsstring)) = 0.1.0
Provides: bundled(crate(num-conv)) = 0.1.0
Provides: bundled(crate(num_cpus)) = 1.16.0
Provides: bundled(crate(num-derive)) = 0.4.2
Provides: bundled(crate(num-integer)) = 0.1.45
Provides: bundled(crate(num-traits)) = 0.2.19
Provides: bundled(crate(object)) = 0.36.4
Provides: bundled(crate(oblivious_http)) = 0.1.0
Provides: bundled(crate(ohttp)) = 0.5.1
Provides: bundled(crate(once_cell)) = 1.21.3
Provides: bundled(crate(ordered-float)) = 3.4.0
Provides: bundled(crate(origin-trials-ffi)) = 0.1.0
Provides: bundled(crate(origin-trial-token)) = 0.1.1
Provides: bundled(crate(oxilangtag)) = 0.1.3
Provides: bundled(crate(oxilangtag-ffi)) = 0.1.0
Provides: bundled(crate(parking_lot)) = 0.12.3
Provides: bundled(crate(parking_lot_core)) = 0.9.10
Provides: bundled(crate(paste)) = 1.0.11
Provides: bundled(crate(payload-support)) = 0.1.0
Provides: bundled(crate(peek-poke)) = 0.3.0
Provides: bundled(crate(peek-poke-derive)) = 0.3.0
Provides: bundled(crate(percent-encoding)) = 2.3.1
Provides: bundled(crate(phf)) = 0.11.2
Provides: bundled(crate(phf_codegen)) = 0.11.2
Provides: bundled(crate(phf_generator)) = 0.11.2
Provides: bundled(crate(phf_macros)) = 0.11.2
Provides: bundled(crate(phf_shared)) = 0.11.2
Provides: bundled(crate(pin-project-lite)) = 0.2.14
Provides: bundled(crate(pin-utils)) = 0.1.0
Provides: bundled(crate(pkcs11-bindings)) = 0.1.5
Provides: bundled(crate(pkg-config)) = 0.3.26
Provides: bundled(crate(plain)) = 0.2.3
Provides: bundled(crate(plane-split)) = 0.18.0
Provides: bundled(crate(powerfmt)) = 0.2.0
Provides: bundled(crate(ppv-lite86)) = 0.2.17
Provides: bundled(crate(precomputed-hash)) = 0.1.1
Provides: bundled(crate(prefs_parser)) = 0.0.1
Provides: bundled(crate(prio)) = 0.16.2
Provides: bundled(crate(processtools)) = 0.1.0
Provides: bundled(crate(proc-macro2)) = 1.0.85
Provides: bundled(crate(proc-macro2)) = 1.0.86
Provides: bundled(crate(profiler_helper)) = 0.1.0
Provides: bundled(crate(profiler-macros)) = 0.1.0
Provides: bundled(crate(profiling)) = 1.0.7
Provides: bundled(crate(prost)) = 0.12.1
Provides: bundled(crate(prost-derive)) = 0.12.1
Provides: bundled(crate(pulse)) = 0.3.0
Provides: bundled(crate(pulse-ffi)) = 0.1.0
Provides: bundled(crate(qcms)) = 0.3.0
Provides: bundled(crate(qlog)) = 0.15.2
Provides: bundled(crate(quick-error)) = 1.2.3
Provides: bundled(crate(quinn-udp)) = 0.5.12
Provides: bundled(crate(quote)) = 1.0.35
Provides: bundled(crate(quote)) = 1.0.40
Provides: bundled(crate(rand)) = 0.8.5
Provides: bundled(crate(rand_chacha)) = 0.3.1
Provides: bundled(crate(rand_core)) = 0.6.4
Provides: bundled(crate(rand_distr)) = 0.4.3
Provides: bundled(crate(raw-window-handle)) = 0.6.2
Provides: bundled(crate(rayon)) = 1.10.0
Provides: bundled(crate(rayon-core)) = 1.12.1
Provides: bundled(crate(regex)) = 1.9.4
Provides: bundled(crate(regex-automata)) = 0.3.7
Provides: bundled(crate(regex-syntax)) = 0.7.5
Provides: bundled(crate(relevancy)) = 0.1.0
Provides: bundled(crate(remote_settings)) = 0.1.0
Provides: bundled(crate(replace_with)) = 0.1.7
Provides: bundled(crate(ringbuf)) = 0.2.8
Provides: bundled(crate(rkv)) = 0.19.0
Provides: bundled(crate(rmp)) = 0.8.14
Provides: bundled(crate(rmp-serde)) = 1.3.0
Provides: bundled(crate(ron)) = 0.10.1
Provides: bundled(crate(rsclientcerts)) = 0.1.0
Provides: bundled(crate(rsdparsa_capi)) = 0.1.0
Provides: bundled(crate(runloop)) = 0.1.0
Provides: bundled(crate(rure)) = 0.2.2
Provides: bundled(crate(rusqlite)) = 0.31.999
Provides: bundled(crate(rusqlite)) = 0.33.0
Provides: bundled(crate(rust_cascade)) = 1.5.0
Provides: bundled(crate(rustc-demangle)) = 0.1.21
Provides: bundled(crate(rustc-hash)) = 1.999.999
Provides: bundled(crate(rustc-hash)) = 2.1.1
Provides: bundled(crate(rustc_version)) = 0.4.0
Provides: bundled(crate(rust_decimal)) = 1.28.1
Provides: bundled(crate(rustix)) = 0.37.19
Provides: bundled(crate(rustix)) = 0.38.39
Provides: bundled(crate(rustversion)) = 1.0.19
Provides: bundled(crate(ryu)) = 1.0.12
Provides: bundled(crate(ryu)) = 1.0.13
Provides: bundled(crate(same-file)) = 1.0.6
Provides: bundled(crate(scopeguard)) = 1.1.0
Provides: bundled(crate(scroll)) = 0.12.0
Provides: bundled(crate(scroll_derive)) = 0.12.0
Provides: bundled(crate(search)) = 0.1.0
Provides: bundled(crate(selectors)) = 0.26.0
Provides: bundled(crate(self_cell)) = 0.10.2
Provides: bundled(crate(semver)) = 1.0.16
Provides: bundled(crate(serde)) = 1.0.163
Provides: bundled(crate(serde)) = 1.0.219
Provides: bundled(crate(serde_bytes)) = 0.11.9
Provides: bundled(crate(serde_cbor)) = 0.11.2
Provides: bundled(crate(serde_derive)) = 1.0.163
Provides: bundled(crate(serde_derive)) = 1.0.219
Provides: bundled(crate(serde_json)) = 1.0.140
Provides: bundled(crate(serde_json)) = 1.0.96
Provides: bundled(crate(serde_path_to_error)) = 0.1.11
Provides: bundled(crate(serde_spanned)) = 0.6.8
Provides: bundled(crate(serde_with)) = 3.12.0
Provides: bundled(crate(serde_with_macros)) = 3.12.0
Provides: bundled(crate(servo_arc)) = 0.4.0
Provides: bundled(crate(sfv)) = 0.9.4
Provides: bundled(crate(sha1)) = 0.10.5
Provides: bundled(crate(sha2)) = 0.10.8
Provides: bundled(crate(sha3)) = 0.10.8
Provides: bundled(crate(shlex)) = 1.3.0
Provides: bundled(crate(signature_cache)) = 0.1.0
Provides: bundled(crate(siphasher)) = 0.3.10
Provides: bundled(crate(slab)) = 0.4.8
Provides: bundled(crate(smallbitvec)) = 2.5.1
Provides: bundled(crate(smallvec)) = 1.13.1
Provides: bundled(crate(smawk)) = 0.3.2
Provides: bundled(crate(socket2)) = 0.4.999
Provides: bundled(crate(socket2)) = 0.5.7
Provides: bundled(crate(spirv)) = 0.3.0+sdk-1.3.268.0
Provides: bundled(crate(sql-support)) = 0.1.0
Provides: bundled(crate(stable_deref_trait)) = 1.2.0
Provides: bundled(crate(static_assertions)) = 1.1.0
Provides: bundled(crate(static_prefs)) = 0.1.0
Provides: bundled(crate(storage)) = 0.1.0
Provides: bundled(crate(storage_variant)) = 0.1.0
Provides: bundled(crate(strck)) = 0.1.2
Provides: bundled(crate(strck_ident)) = 0.1.2
Provides: bundled(crate(strsim)) = 0.11.1
Provides: bundled(crate(strum)) = 0.27.1
Provides: bundled(crate(strum_macros)) = 0.27.1
Provides: bundled(crate(style)) = 0.0.1
Provides: bundled(crate(style_derive)) = 0.0.1
Provides: bundled(crate(style_traits)) = 0.0.1
Provides: bundled(crate(subtle)) = 2.5.0
Provides: bundled(crate(suggest)) = 0.1.0
Provides: bundled(crate(svg_fmt)) = 0.4.1
Provides: bundled(crate(swgl)) = 0.1.0
Provides: bundled(crate(syn)) = 2.0.87
Provides: bundled(crate(sync15)) = 0.1.0
Provides: bundled(crate(sync-guid)) = 0.1.0
Provides: bundled(crate(synstructure)) = 0.13.1
Provides: bundled(crate(tabs)) = 0.1.0
Provides: bundled(crate(tempfile)) = 3.16.0
Provides: bundled(crate(tempfile)) = 3.5.0
Provides: bundled(crate(termcolor)) = 1.4.1
Provides: bundled(crate(textwrap)) = 0.16.1
Provides: bundled(crate(thin-vec)) = 0.2.12
Provides: bundled(crate(thiserror)) = 1.999.999
Provides: bundled(crate(thiserror)) = 2.0.9
Provides: bundled(crate(thiserror-impl)) = 2.0.9
Provides: bundled(crate(threadbound)) = 0.1.5
Provides: bundled(crate(time)) = 0.1.45
Provides: bundled(crate(time)) = 0.3.36
Provides: bundled(crate(time-core)) = 0.1.2
Provides: bundled(crate(time-macros)) = 0.2.18
Provides: bundled(crate(tinystr)) = 0.7.6
Provides: bundled(crate(tinyvec)) = 1.9.0
Provides: bundled(crate(tinyvec_macros)) = 0.1.1
Provides: bundled(crate(toml)) = 0.5.11
Provides: bundled(crate(toml)) = 0.8.22
Provides: bundled(crate(toml_datetime)) = 0.6.9
Provides: bundled(crate(toml_edit)) = 0.22.26
Provides: bundled(crate(toml_write)) = 0.1.1
Provides: bundled(crate(topological-sort)) = 0.1.0
Provides: bundled(crate(to_shmem)) = 0.1.0
Provides: bundled(crate(to_shmem_derive)) = 0.1.0
Provides: bundled(crate(tracy-rs)) = 0.1.2
Provides: bundled(crate(trust-anchors)) = 0.1.0
Provides: bundled(crate(typed-arena-nomut)) = 0.1.0
Provides: bundled(crate(type-map)) = 0.4.0
Provides: bundled(crate(typenum)) = 1.16.0
Provides: bundled(crate(types)) = 0.1.0
Provides: bundled(crate(uluru)) = 3.0.0
Provides: bundled(crate(unicase)) = 2.6.0
Provides: bundled(crate(unic-langid)) = 0.9.5
Provides: bundled(crate(unic-langid-ffi)) = 0.1.0
Provides: bundled(crate(unic-langid-impl)) = 0.9.5
Provides: bundled(crate(unicode-bidi)) = 0.3.15
Provides: bundled(crate(unicode-bidi-ffi)) = 0.1.0
Provides: bundled(crate(unicode-ident)) = 1.0.6
Provides: bundled(crate(unicode-ident)) = 1.0.8
Provides: bundled(crate(unicode-normalization)) = 0.1.24
Provides: bundled(crate(unicode-width)) = 0.1.999
Provides: bundled(crate(unicode-width)) = 0.2.0
Provides: bundled(crate(uniffi)) = 0.29.2
Provides: bundled(crate(uniffi_bindgen)) = 0.29.2
Provides: bundled(crate(uniffi_build)) = 0.29.2
Provides: bundled(crate(uniffi_core)) = 0.29.2
Provides: bundled(crate(uniffi_internal_macros)) = 0.29.2
Provides: bundled(crate(uniffi_macros)) = 0.29.2
Provides: bundled(crate(uniffi_meta)) = 0.29.2
Provides: bundled(crate(uniffi_pipeline)) = 0.29.2
Provides: bundled(crate(uniffi_udl)) = 0.29.2
Provides: bundled(crate(url)) = 2.5.4
Provides: bundled(crate(utf16_iter)) = 1.0.5
Provides: bundled(crate(utf8_iter)) = 1.0.4
Provides: bundled(crate(utf8parse)) = 0.2.2
Provides: bundled(crate(uuid)) = 1.3.0
Provides: bundled(crate(vcpkg)) = 0.2.999
Provides: bundled(crate(version_check)) = 0.9.4
Provides: bundled(crate(viaduct)) = 0.1.0
Provides: bundled(crate(void)) = 1.0.2
Provides: bundled(crate(walkdir)) = 2.3.2
Provides: bundled(crate(wasm-encoder)) = 0.219.1
Provides: bundled(crate(wast)) = 219.0.1
Provides: bundled(crate(webext-storage)) = 0.1.0
Provides: bundled(crate(webrender)) = 0.62.0
Provides: bundled(crate(webrender_api)) = 0.62.0
Provides: bundled(crate(webrender_bindings)) = 0.1.0
Provides: bundled(crate(webrender_build)) = 0.0.2
Provides: bundled(crate(webrtc-sdp)) = 0.3.13
Provides: bundled(crate(weedle2)) = 5.0.0
Provides: bundled(crate(wgpu_bindings)) = 0.1.0
Provides: bundled(crate(wgpu-core)) = 25.0.0
Provides: bundled(crate(wgpu-core-deps-windows-linux-android)) = 25.0.0
Provides: bundled(crate(wgpu-hal)) = 25.0.0
Provides: bundled(crate(wgpu-types)) = 25.0.0
Provides: bundled(crate(whatsys)) = 0.3.1
Provides: bundled(crate(winnow)) = 0.7.10
Provides: bundled(crate(winnow)) = 0.7.9
Provides: bundled(crate(wpf-gpu-raster)) = 0.1.0
Provides: bundled(crate(wr_glyph_rasterizer)) = 0.1.0
Provides: bundled(crate(write16)) = 1.0.0
Provides: bundled(crate(writeable)) = 0.5.5
Provides: bundled(crate(wr_malloc_size_of)) = 0.2.1
Provides: bundled(crate(xmldecl)) = 0.2.0
Provides: bundled(crate(xml-rs)) = 0.8.4
Provides: bundled(crate(xpcom)) = 0.1.0
Provides: bundled(crate(xpcom_macros)) = 0.1.0
Provides: bundled(crate(yoke)) = 0.7.4
Provides: bundled(crate(yoke-derive)) = 0.7.4
Provides: bundled(crate(zeitstempel)) = 0.1.1
Provides: bundled(crate(zerocopy)) = 0.7.32
Provides: bundled(crate(zerofrom)) = 0.1.4
Provides: bundled(crate(zerofrom-derive)) = 0.1.3
Provides: bundled(crate(zeroize)) = 1.8.1
Provides: bundled(crate(zeroize_derive)) = 1.4.2
Provides: bundled(crate(zerovec)) = 0.10.4
Provides: bundled(crate(zerovec-derive)) = 0.10.3

%description
Mozilla Firefox is an open-source web browser, designed for standards
compliance, performance and portability.

%if 0%{?run_firefox_tests}
%global testsuite_pkg_name %{name}-testresults
%package -n %{testsuite_pkg_name}
Summary: Results of testsuite
%description -n %{testsuite_pkg_name}
This package contains results of tests executed during build.
%files -n %{testsuite_pkg_name}
/%{version}-%{release}/test_results
/%{version}-%{release}/test_summary.txt
/%{version}-%{release}/failures-*
%endif

%if 0%{?rhel} >= 9
%package x11
Summary: Firefox X11 launcher.
Requires: %{name} = %{version}-%{release}
%description x11
The firefox-x11 package contains launcher and desktop file
to run Firefox explicitly on X11.
%files x11
%{_bindir}/firefox-x11
%{_datadir}/applications/firefox-x11.desktop
%endif

#---------------------------------------------------------------------

%prep
echo "Build environment"
echo "--------------------------------------------"
echo "dist                %{?dist}"
echo "RHEL minor version: %{?rhel_minor_version}"
echo "bundle_nss          %{?bundle_nss}"
echo "system_nss          %{?system_nss}"
echo "use_dts             %{?use_dts}"
echo "use_nodejs_scl      %{?use_nodejs_scl}"
echo "use_python3_scl     %{?use_python3_scl}"
echo "with_wasi_sdk       %{?with_wasi_sdk}"
echo "use_gcc_ts          %{?use_gcc_ts}"
echo "--------------------------------------------"
#clang -print-search-dirs
%setup -q -n %{name}-%{version}

%if %{with_wasi_sdk}
%setup -q -T -D -a 50
%endif

# ---- RHEL specific patches ---
# -- Downstream only --
%patch -P1 -p1 -b .disable-elfhack
%patch -P2 -p1 -b .firefox-gcc-build
%patch -P3 -p1 -b .build-big-endian-errors

%if 0%{?rhel} == 7
%patch -P4 -p1 -b .build-rhel7-lower-node-min-version
# Disable gamepad due to old kernel
%patch -P10 -p1 -b .gamepad
  %ifarch ppc64
  # abiv2 version not available in RHEL7 ppc
  # TODO most likely not needed with system nss
%patch -P5 -p1 -b .ppc64-abiv2
  %endif
  %ifarch %{ix86}
  # -F dwarf not available in RHEL7's nasm
%patch -P6 -p1 -b .build-rhel7-nasm-dwarf
  %endif
%endif
%patch -P8 -p1 -b .rhbz-2131158-webrtc-nss-fix
%patch -P9 -p1 -b .build-ffvpx
%patch -P11 -p1 -b .rhbz-71999-fips-youtube

%if %{?system_pipewire}
%patch -P13 -p1 -b .fix-build-with-system-pipewire
%endif

%if %{?system_nss}
%patch -P14 -p1 -b .system-nss
%endif

# We need to create the wasi.patch with the correct path to the wasm libclang_rt.
%if %{with_wasi_sdk}
export LIBCLANG_RT=`pwd`/wasi-sdk-20/build/compiler-rt/lib/wasi/libclang_rt.builtins-wasm32.a; cat %{SOURCE38} | envsubst > %{_sourcedir}/wasi.patch
%patch -P203 -p1 -b .wasi
%endif

# -- Upstreamed patches --
%patch -P51 -p1 -b .mozilla-bmo1170092
%patch -P52 -p1 -b .exceptionHandled-for-IO-error-processhandler
%patch -P53 -p1 -b .clear-lang-bundles
%patch -P54 -p1 -b .restoreWinState
%patch -P55 -p1 -b .D266159.1760530435

# -- Submitted upstream, not merged --
%patch -P101 -p1 -b .mozilla-bmo1636168-fscreen
%patch -P102 -p1 -b .mozilla-bmo1670333
%patch -P103 -p1 -b .mozilla-bmo1504834-part1
%patch -P104 -p1 -b .mozilla-bmo1504834-part3
%patch -P105 -p1 -b .mozilla-bmo849632
%patch -P106 -p1 -b .mozilla-bmo998749
%patch -P107 -p1 -b .mozilla-bmo1716707-swizzle
%patch -P108 -p1 -b .mozilla-bmo1716707-svg

%if 0%{?rhel} == 7 || (0%{?rhel} == 8 && %{rhel_minor_version} < 4)
%patch -P109 -p1 -b .mozilla-bmo1789216-disable-av1
%endif
%patch -P110 -p1 -b .libaom
%patch -P111 -p1 -b .av1-else-condition-add

%if 0%{?rhel} >= 10
# ML-DSA support
%patch -P120 -p1 -b .integrate-ml-dsa-signature-verification-for-pkix-certificate-chain-validation
%patch -P121 -p1 -b .add-ml-dsa-certificate-support-to-certviewer
%patch -P122 -p1 -b .enable-ml-dsa-signature-verification-for-certificate-chain-validation
%patch -P123 -p1 -b .adapt-ml-dsa-support-to-rhel-nss
%patch -P124 -p1 -b .enable-ml-dsa-in-manager-ssl
%patch -P125 -p1 -b .add-mlkem768-secp256r1-support
%endif

# ---- Fedora specific patches ----
%patch -P151 -p1 -b .addons
%patch -P152 -p1 -b .rhbz-1173156
%patch -P153 -p1 -b .addons-nss-hack
# ARM run-time patch
%ifarch aarch64
%patch -P154 -p1 -b .rhbz-1354671
%endif

# Fips webrtc patch
%ifnarch ppc64 ppc64le s390x
%patch -P200 -p1 -b .D225034.1750779491
%patch -P201 -p1 -b .D224587
%patch -P202 -p1 -b .D224588
%endif

# ---- Security patches ----

%{__rm} -f .mozconfig
%{__cp} %{SOURCE10} .mozconfig
%{__cp} %{SOURCE24} mozilla-api-key
%{__cp} %{SOURCE27} google-api-key
%{__cp} %{SOURCE35} google-loc-api-key

echo "ac_add_options --prefix=\"%{_prefix}\"" >> .mozconfig
echo "ac_add_options --libdir=\"%{_libdir}\"" >> .mozconfig

%if %{?system_nss}
echo "ac_add_options --with-system-nspr" >> .mozconfig
echo "ac_add_options --with-system-nss" >> .mozconfig
%else
echo "ac_add_options --without-system-nspr" >> .mozconfig
echo "ac_add_options --without-system-nss" >> .mozconfig
%endif

%if %{?system_drm}
echo "ac_add_options --with-system-libdrm" >> .mozconfig
%else
echo "ac_add_options --without-system-libdrm" >> .mozconfig
%endif

%if %{?system_gbm}
echo "ac_add_options --with-system-gbm" >> .mozconfig
%else
echo "ac_add_options --without-system-gbm" >> .mozconfig
%endif

%if %{?system_pipewire}
echo "ac_add_options --with-system-pipewire" >> .mozconfig
%else
echo "ac_add_options --without-system-pipewire" >> .mozconfig
%endif

%if %{?debug_build}
echo "ac_add_options --enable-debug" >> .mozconfig
echo "ac_add_options --disable-optimize" >> .mozconfig
%else
%global optimize_flags "none"

%if 0%{?rhel} < 10
  %ifarch s390x
   %global optimize_flags "-g -O1"
  %endif
%endif

%ifarch ppc64le aarch64
%global optimize_flags "-g -O2"
%endif
%if %{optimize_flags} != "none"
echo 'ac_add_options --enable-optimize=%{?optimize_flags}' >> .mozconfig
%else
echo 'ac_add_options --enable-optimize' >> .mozconfig
%endif
echo "ac_add_options --disable-debug" >> .mozconfig
%endif

# Second arches fail to start with jemalloc enabled
%ifnarch %{ix86} x86_64
echo "ac_add_options --disable-jemalloc" >> .mozconfig
%endif

%if 0%{?build_tests}
echo "ac_add_options --enable-tests" >> .mozconfig
%else
echo "ac_add_options --disable-tests" >> .mozconfig
%endif

%if %{?system_libvpx}
echo "ac_add_options --with-system-libvpx" >> .mozconfig
%else
echo "ac_add_options --without-system-libvpx" >> .mozconfig
%endif

%ifarch s390x
echo "ac_add_options --disable-jit" >> .mozconfig
%endif

%ifarch ppc64 ppc64le
echo "ac_add_options --disable-webrtc" >> .mozconfig
%endif
%if 0%{?rhel} < 10
echo "ac_add_options --disable-lto" >> .mozconfig
%endif

# AV1 requires newer nasm that was rebased in 8.4
%if 0%{?rhel} == 7 || (0%{?rhel} == 8 && %{rhel_minor_version} < 4)
echo "ac_add_options --disable-av1" >> .mozconfig
%endif

# api keys full path
echo "ac_add_options --with-mozilla-api-keyfile=`pwd`/mozilla-api-key" >> .mozconfig
echo "ac_add_options --with-google-location-service-api-keyfile=`pwd`/google-loc-api-key" >> .mozconfig
echo "ac_add_options --with-google-safebrowsing-api-keyfile=`pwd`/google-api-key" >> .mozconfig

# May result in empty --with-libclang-path= in earlier versions.
# So far this is needed only for c8s/c9s.
# Clang 17 upstream's detection fails, tell it where to look.
echo "ac_add_options --with-libclang-path=`llvm-config --libdir`" >> .mozconfig

%if %{with_wasi_sdk}
echo "ac_add_options --with-wasi-sysroot=`pwd`/wasi-sdk-20/build/install/opt/wasi-sdk/share/wasi-sysroot" >> .mozconfig
%else
echo "ac_add_options --without-sysroot" >> .mozconfig
echo "ac_add_options --without-wasm-sandboxed-libraries" >> .mozconfig
%endif

echo 'export NODEJS="%{_buildrootdir}/bin/node-stdout-nonblocking-wrapper"' >> .mozconfig

# Remove executable bit to make brp-mangle-shebangs happy.
chmod -x third_party/rust/itertools/src/lib.rs
chmod a-x third_party/rust/ash/src/extensions/ext/*.rs
chmod a-x third_party/rust/ash/src/extensions/khr/*.rs
chmod a-x third_party/rust/ash/src/extensions/nv/*.rs

mkdir %{_buildrootdir}/bin || :
cp %{SOURCE32} %{_buildrootdir}/bin || :

#---------------------------------------------------------------------

%build
# TODO: causes SIGSEGV on the webrender compilation, we might remove it with newer rust version
# Disable LTO to work around rhbz#1883904
%define _lto_cflags %{nil}

#WASI SDK
%if %{with_wasi_sdk}
pushd wasi-sdk-20
sed -i -e "s|VERSION=.*|VERSION=20|g" tar_from_installation.sh
cat tar_from_installation.sh
NINJA_FLAGS=-v CC=clang CXX=clang++ env -u CFLAGS -u CXXFLAGS -u FFLAGS -u VALFLAGS -u RUSTFLAGS -u LDFLAGS -u LT_SYS_LIBRARY_PATH make package
popd
%endif

export PATH="%{_buildrootdir}/bin:$PATH"
# Cleanup buildroot for existing rpms from bundled nss/nspr and other packages
rm -rf %{_buildrootdir}/* FIXME?

function install_rpms_to_current_dir() {
    PACKAGE_RPM=$(eval echo $1)
    PACKAGE_DIR=%{_rpmdir}

    if [ ! -f $PACKAGE_DIR/$PACKAGE_RPM ]; then
        # Hack for tps tests
        ARCH_STR=%{_arch}
        %ifarch %{ix86}
            ARCH_STR="i?86"
        %endif
        PACKAGE_DIR="$PACKAGE_DIR/$ARCH_STR"
     fi

     for package in $(ls $PACKAGE_DIR/$PACKAGE_RPM)
     do
         echo "$package"
         rpm2cpio "$package" | cpio -ivdu
     done
}

%if 0%{?bundle_nss}
%if 0%{?rhel} == 8
  # nspr
  rpm -ivh %{SOURCE402}
  rpmbuild --nodeps --define '_prefix %{bundled_install_path}' --without=tests -ba %{_specdir}/nspr.spec
  pushd %{_buildrootdir}
  install_rpms_to_current_dir nspr-4*.rpm
  install_rpms_to_current_dir nspr-devel*.rpm
  popd
  echo "Setting nspr flags"
  # nss-setup-flags-env.inc
  sed -i 's@%{bundled_install_path}@%{_buildrootdir}%{bundled_install_path}@g' %{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig/nspr*.pc

  export LDFLAGS="-L%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
  export LDFLAGS="-Wl,-rpath,%{bundled_install_path}/%{_lib} $LDFLAGS"
  export LDFLAGS="-Wl,-rpath-link,%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
  export PKG_CONFIG_PATH=%{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig
  export PATH="%{_buildrootdir}%{bundled_install_path}/bin:$PATH"

  export PATH=%{_buildrootdir}/%{bundled_install_path}/bin:$PATH
  rpm -ivh %{SOURCE403}

%else
  rpm -ivh %{SOURCE404}
%endif
  # nss
  rpmbuild --nodeps --define '_prefix %{bundled_install_path}' --without=tests -ba %{_specdir}/nss.spec
  pushd %{_buildrootdir}
  #cleanup
  install_rpms_to_current_dir nss-3*.rpm
  install_rpms_to_current_dir nss-devel*.rpm
  install_rpms_to_current_dir nss-pkcs11-devel*.rpm
  install_rpms_to_current_dir nss-softokn-3*.rpm
  install_rpms_to_current_dir nss-softokn-devel*.rpm
  install_rpms_to_current_dir nss-softokn-freebl-3*.rpm
  install_rpms_to_current_dir nss-softokn-freebl-devel*.rpm
  install_rpms_to_current_dir nss-util-3*.rpm
  install_rpms_to_current_dir nss-util-devel*.rpm
%if 0%{?rhel} > 8

  install_rpms_to_current_dir nspr-4*.rpm
  install_rpms_to_current_dir nspr-devel*.rpm
  sed -i 's@%{bundled_install_path}@%{_buildrootdir}%{bundled_install_path}@g' %{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig/nspr*.pc
%endif
  popd
  %filter_provides_in %{bundled_install_path}/%{_lib}
  %filter_requires_in %{bundled_install_path}/%{_lib}
  %filter_from_requires /libnss3.so.*/d
  %filter_from_requires /libsmime3.so.*/d
  %filter_from_requires /libssl3.so.*/d
  %filter_from_requires /libnssutil3.so.*/d
  %filter_from_requires /libnspr4.so.*/d

  export LDFLAGS="-L%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
  export LDFLAGS="-Wl,-rpath,%{bundled_install_path}/%{_lib} $LDFLAGS"
  export LDFLAGS="-Wl,-rpath-link,%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
  export PKG_CONFIG_PATH=%{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig
  export PATH="%{_buildrootdir}%{bundled_install_path}/bin:$PATH"
%endif

# Enable toolsets
set +e
%if 0%{?use_gcc_ts}
source scl_source enable gcc-toolset-%{gts_version}
%endif
%if 0%{?use_dts}
source scl_source enable devtoolset-%{dts_version}
%endif
%if 0%{?use_nodejs_scl}
source scl_source enable rh-nodejs10
%endif
%if 0%{?use_python3_scl}
source scl_source enable rh-python38
%endif

set -e
env
which gcc
which c++
which g++
which ld
which nasm
which node
which python3
# Bundled cbindgen
mkdir -p my_rust_vendor
cd my_rust_vendor
%{__tar} xf %{SOURCE2}
mkdir -p .cargo
cat > .cargo/config <<EOL
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "`pwd`"
EOL

%ifarch aarch64
#export RUSTFLAGS="-Cdebuginfo=0 -Clinker=/opt/rh/gcc-toolset-12/root/usr/bin/gcc"
%endif

env CARGO_HOME=.cargo cargo install cbindgen
export PATH=`pwd`/.cargo/bin:$PATH
cd -

# end of Bundled cbindgen

mkdir %{_buildrootdir}/bin || :
cp %{SOURCE32} %{_buildrootdir}/bin || :

# Update the various config.guess to upstream release for aarch64 support
# Do not update config.guess in the ./third_party/rust because that would break checksums
find ./ -path ./third_party/rust -prune -o -name config.guess -exec cp /usr/lib/rpm/config.guess {} ';'

MOZ_OPT_FLAGS=$(echo "%{optflags}" | %{__sed} -e 's/-Wall//' | %{__sed} -e 's/-fexceptions//' )
#rhbz#1037063
# -Werror=format-security causes build failures when -Wno-format is explicitly given
# for some sources
# Explicitly force the hardening flags for Firefox so it passes the checksec test;
# See also https://fedoraproject.org/wiki/Changes/Harden_All_Packages
# Workaround for mozbz#1531309
MOZ_OPT_FLAGS=$(echo "$MOZ_OPT_FLAGS" | %{__sed} -e 's/-Werror=format-security//')

MOZ_OPT_FLAGS="$MOZ_OPT_FLAGS -fPIC -Wl,-z,relro -Wl,-z,now"
%if %{?debug_build}
MOZ_OPT_FLAGS=$(echo "$MOZ_OPT_FLAGS" | %{__sed} -e 's/-O2//')
%endif

%ifarch %{ix86}
MOZ_OPT_FLAGS=$(echo "$MOZ_OPT_FLAGS" | %{__sed} -e 's/-g/-g0/')
export MOZ_DEBUG_FLAGS=" "
%endif

%ifarch s390x aarch64 %{ix86}
MOZ_LINK_FLAGS="-Wl,--no-keep-memory -Wl,--reduce-memory-overheads"
%endif

%if 0%{?flatpak}
# Make sure the linker can find libraries in /app/lib64 as we don't use
# __global_ldflags that normally sets this.
MOZ_LINK_FLAGS="$MOZ_LINK_FLAGS -L%{_libdir}"
%endif
%ifarch %{ix86} s390x
export RUSTFLAGS="-Cdebuginfo=0"
echo 'export RUSTFLAGS="-Cdebuginfo=0"' >> .mozconfig
%endif

%if 0%{?bundle_nss}
  mkdir -p %{_buildrootdir}%{bundled_install_path}/%{_lib}
  MOZ_LINK_FLAGS="-L%{_buildrootdir}%{bundled_install_path}/%{_lib} $MOZ_LINK_FLAGS"
  MOZ_LINK_FLAGS="-Wl,-rpath,%{bundled_install_path}/%{_lib} $MOZ_LINK_FLAGS"
  MOZ_LINK_FLAGS="-Wl,-rpath-link,%{_buildrootdir}%{bundled_install_path}/%{_lib} $MOZ_LINK_FLAGS"
%endif

# We don't wantfirefox to use CK_GCM_PARAMS_V3 in nss
MOZ_OPT_FLAGS="$MOZ_OPT_FLAGS -DNSS_PKCS11_3_0_STRICT"

echo "export CFLAGS=\"$MOZ_OPT_FLAGS\"" >> .mozconfig
echo "export CXXFLAGS=\"$MOZ_OPT_FLAGS\"" >> .mozconfig
%ifarch aarch64
echo "export ASFLAGS=\"-mbranch-protection=standard\"" >> .mozconfig
%endif
%ifarch x86_64
echo "export ASFLAGS=\"-fcf-protection=full\"" >> .mozconfig
%endif

echo "export LDFLAGS=\"$MOZ_LINK_FLAGS\"" >> .mozconfig
echo "export CC=gcc" >> .mozconfig
echo "export CXX=g++" >> .mozconfig
echo "export AR=\"gcc-ar\"" >> .mozconfig
echo "export NM=\"gcc-nm\"" >> .mozconfig
echo "export RANLIB=\"gcc-ranlib\"" >> .mozconfig
echo "export MALLOC_MMAP_MAX_=0" >> .mozconfig

MOZ_SMP_FLAGS=-j1
# On x86_64 architectures, Mozilla can build up to 4 jobs at once in parallel,
# however builds tend to fail on other arches when building in parallel.
#%ifarch %{ix86} s390x aarch64 ppc64le
#[ -z "$RPM_BUILD_NCPUS" ] && \
#     RPM_BUILD_NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"
#[ "$RPM_BUILD_NCPUS" -ge 2 ] && MOZ_SMP_FLAGS=-j2
#%endif
#%ifarch x86_64 ppc ppc64 ppc64le
[ -z "$RPM_BUILD_NCPUS" ] && \
       RPM_BUILD_NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"
[ "$RPM_BUILD_NCPUS" -ge 2 ] && MOZ_SMP_FLAGS=-j2
[ "$RPM_BUILD_NCPUS" -ge 4 ] && MOZ_SMP_FLAGS=-j4
[ "$RPM_BUILD_NCPUS" -ge 8 ] && MOZ_SMP_FLAGS=-j8
[ "$RPM_BUILD_NCPUS" -ge 16 ] && MOZ_SMP_FLAGS=-j16
#%endif

echo "mk_add_options MOZ_MAKE_FLAGS=\"$MOZ_SMP_FLAGS\"" >> .mozconfig
echo "mk_add_options MOZ_SERVICES_SYNC=1" >> .mozconfig
echo "export STRIP=/bin/true" >> .mozconfig

%if %{launch_wayland_compositor}
cp %{SOURCE36} .
. ./testing.sh run_wayland_compositor
%endif

# We could use %%include, but in %%files, %%post and other sections, but in these
# sections it could lead to syntax errors about unclosed %%if. Work around it by
# using the following macro
%define include_file() %{expand:%(cat '%1')}

%if 0%{?bundle_nss}
  echo "Setting nss flags"
  # nss-setup-flags-env.inc
  %include_file %{SOURCE401}
  export PATH=%{_buildrootdir}/%{bundled_install_path}/bin:$PATH
  echo $PKG_CONFIG_PATH
%endif

./mach build -v 2>&1 || exit 1

#---------------------------------------------------------------------
%install
%if 0%{?rhel} == 7
source scl_source enable devtoolset-11 || :
%endif
export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=system
function install_rpms_to_current_dir() {
    PACKAGE_RPM=$(eval echo $1)
    PACKAGE_DIR=%{_rpmdir}

    if [ ! -f $PACKAGE_DIR/$PACKAGE_RPM ]; then
        # Hack for tps tests
        ARCH_STR=%{_arch}
        %ifarch %{ix86}
            ARCH_STR="i?86"
        %endif
        PACKAGE_DIR="$PACKAGE_DIR/$ARCH_STR"
     fi

     for package in $(ls $PACKAGE_DIR/$PACKAGE_RPM)
     do
         echo "$package"
         rpm2cpio "$package" | cpio -ivdu
     done
}

%if 0%{?bundle_nss}
  pushd %{buildroot}
  install_rpms_to_current_dir nspr-4*.rpm
  install_rpms_to_current_dir nss-3*.rpm
  install_rpms_to_current_dir nss-softokn-3*.rpm
  install_rpms_to_current_dir nss-softokn-freebl-3*.rpm
  install_rpms_to_current_dir nss-util-3*.rpm

  # cleanup unecessary nss files
  rm -rf %{buildroot}/%{bundled_install_path}/lib/dracut
  rm -rf %{buildroot}/%{bundled_install_path}/%{_lib}/nss
  rm -rf %{buildroot}/%{bundled_install_path}/%{_lib}/share
  rm -rf %{buildroot}/%{bundled_install_path}/share
  rm -rf %{buildroot}/etc/pki
  rm -rf %{buildroot}/usr/lib/.build-id
  rm -rf %{buildroot}/etc/crypto-policies
  popd
%endif

# run Firefox test suite
%if %{launch_wayland_compositor}
cp %{SOURCE36} .
. ./testing.sh run_wayland_compositor
%endif

%if 0%{?run_firefox_tests}
  mkdir -p objdir/_virtualenvs/init_py3
  %{__cat} > objdir/_virtualenvs/init_py3/pip.conf << EOF
[global]
find-links=`pwd`/mochitest-python
no-index=true
EOF
  tar xf %{SOURCE37}
  cp %{SOURCE36} .
  mkdir -p test_results
  %if %{?test_on_wayland}
    ./testing.sh run_tests_wayland || true
  %else
    ./testing.sh run_tests_x11 || true
  %endif
  ./testing.sh print_results > test_summary.txt 2>&1 || true
  ./testing.sh print_failures || true
%endif

# set up our default bookmarks
%if !0%{?flatpak}
  %global default_bookmarks_file  /usr/share/bookmarks/default-bookmarks.html
  %{__cp} -p %{default_bookmarks_file} objdir/dist/bin/browser/chrome/browser/content/browser/default-bookmarks.html
%endif

# Make sure locale works for langpacks
%{__cat} > objdir/dist/bin/browser/defaults/preferences/firefox-l10n.js << EOF
pref("general.useragent.locale", "chrome://global/locale/intl.properties");
EOF

DESTDIR=%{buildroot} make -C objdir install

%{__mkdir_p} %{buildroot}{%{_libdir},%{_bindir},%{_datadir}/applications}

desktop-file-install --dir %{buildroot}%{_datadir}/applications %{SOURCE20}
%if 0%{?rhel} >= 9
desktop-file-install --dir %{buildroot}%{_datadir}/applications %{SOURCE31}
%endif

# set up the firefox start script
%{__rm} -rf %{buildroot}%{_bindir}/firefox
%{__sed} -e 's,/__PREFIX__,%{_prefix},g' %{SOURCE21} > %{buildroot}%{_bindir}/firefox
%{__chmod} 755 %{buildroot}%{_bindir}/firefox

%if 0%{?flatpak}
sed -i -e 's|%FLATPAK_ENV_VARS%|export TMPDIR="$XDG_CACHE_HOME/tmp"|' %{buildroot}%{_bindir}/firefox
%else
sed -i -e 's|%FLATPAK_ENV_VARS%||' %{buildroot}%{_bindir}/firefox
%endif

# Run firefox under wayland only on RHEL9 and newer
%if 0%{?rhel} < 9
sed -i -e 's|%DISABLE_WAYLAND_PLACEHOLDER%|export MOZ_DISABLE_WAYLAND=1|' %{buildroot}%{_bindir}/firefox
%else
sed -i -e 's|%DISABLE_WAYLAND_PLACEHOLDER%||' %{buildroot}%{_bindir}/firefox
# firefox-x11 launch script for RHEL9 only
%{__sed} -e 's,/__PREFIX__,%{_prefix},g' %{SOURCE30} > %{buildroot}%{_bindir}/firefox-x11
%{__chmod} 755 %{buildroot}%{_bindir}/firefox-x11
%endif

%{__install} -p -D -m 644 %{SOURCE23} %{buildroot}%{_mandir}/man1/firefox.1

%{__rm} -f %{buildroot}/%{mozappdir}/firefox-config
%{__rm} -f %{buildroot}/%{mozappdir}/update-settings.ini

for s in 16 22 24 32 48 256; do
    %{__mkdir_p} %{buildroot}%{_datadir}/icons/hicolor/${s}x${s}/apps
    %{__cp} -p browser/branding/official/default${s}.png \
               %{buildroot}%{_datadir}/icons/hicolor/${s}x${s}/apps/firefox.png
done

# Install hight contrast icon
%{__mkdir_p} %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps
%{__cp} -p %{SOURCE25} \
           %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps

echo > %{name}.lang
%if %{with langpacks}
# Extract langpacks, make any mods needed, repack the langpack, and install it.
%{__mkdir_p} %{buildroot}%{langpackdir}
%{__tar} xf %{SOURCE1}
for langpack in `ls firefox-langpacks/*.xpi`; do
  language=`basename $langpack .xpi`
  extensionID=langpack-$language@firefox.mozilla.org
  %{__mkdir_p} $extensionID
  unzip -qq $langpack -d $extensionID
  find $extensionID -type f | xargs chmod 644

  cd $extensionID
  zip -qq -r9mX ../${extensionID}.xpi *
  cd -

  %{__install} -m 644 ${extensionID}.xpi %{buildroot}%{langpackdir}
  language=`echo $language | sed -e 's/-/_/g'`
%if 0%{?flatpak}
  echo "%{langpackdir}/${extensionID}.xpi" >> %{name}.lang
%else
  echo "%%lang($language) %{langpackdir}/${extensionID}.xpi" >> %{name}.lang
%endif
done
%{__rm} -rf firefox-langpacks

# Install langpack workaround (see #707100, #821169)
function create_default_langpack() {
language_long=$1
language_short=$2
cd %{buildroot}%{langpackdir}
ln -s langpack-$language_long@firefox.mozilla.org.xpi langpack-$language_short@firefox.mozilla.org.xpi
cd -
echo "%%lang($language_short) %{langpackdir}/langpack-$language_short@firefox.mozilla.org.xpi" >> %{name}.lang
}

# Table of fallbacks for each language
# please file a bug at bugzilla.redhat.com if the assignment is incorrect
#create_default_langpack "bn-IN" "bn"
create_default_langpack "es-AR" "es"
create_default_langpack "fy-NL" "fy"
create_default_langpack "ga-IE" "ga"
create_default_langpack "gu-IN" "gu"
create_default_langpack "hi-IN" "hi"
create_default_langpack "hy-AM" "hy"
create_default_langpack "nb-NO" "nb"
create_default_langpack "nn-NO" "nn"
create_default_langpack "pa-IN" "pa"
create_default_langpack "pt-PT" "pt"
create_default_langpack "sv-SE" "sv"
create_default_langpack "zh-TW" "zh"
%endif

# Keep compatibility with the old preference location.
%{__mkdir_p} %{buildroot}%{mozappdir}/defaults/preferences
%{__mkdir_p} %{buildroot}%{mozappdir}/browser/defaults
ln -s %{mozappdir}/defaults/preferences $RPM_BUILD_ROOT/%{mozappdir}/browser/defaults/preferences
# Default preferences
%{__cp} %{SOURCE12} %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
sed -i -e 's|%PREFIX%|%{_prefix}|' %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
sed -i -e 's|%HOMEPAGE%|%{homepage}|' %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
# Enable modern crypto for the key export on the RHEL9 only (rhbz#1764205)
%if 0%{?rhel} >= 9
  echo 'pref("security.pki.use_modern_crypto_with_pkcs12", true);' >> %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
%endif

%ifarch s390x
  echo 'pref("gfx.webrender.force-disabled", true);' >> %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
%endif

%ifarch s390x ppc64
  echo 'pref("gfx.webrender.force-disabled", true);' >> %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
%endif

# System config dir
%{__mkdir_p} %{buildroot}/%{_sysconfdir}/%{name}/pref

# System extensions
%global firefox_app_id  \{ec8030f7-c20a-464f-9b0e-13a3a9e97384\}
%{__mkdir_p} %{buildroot}%{_datadir}/mozilla/extensions/%{firefox_app_id}
%{__mkdir_p} %{buildroot}%{_libdir}/mozilla/extensions/%{firefox_app_id}

# Copy over the LICENSE
%{__install} -p -c -m 644 LICENSE %{buildroot}/%{mozappdir}

# Use the system hunspell dictionaries
%{__rm} -rf %{buildroot}%{mozappdir}/dictionaries
ln -s %{_datadir}/myspell %{buildroot}%{mozappdir}/dictionaries

%if 0%{?run_firefox_tests}
%{__mkdir_p} %{buildroot}/%{version}-%{release}/test_results
%{__cp} test_results/* %{buildroot}/%{version}-%{release}/test_results
%{__cp} test_summary.txt %{buildroot}/%{version}-%{release}/
%{__cp} failures-* %{buildroot}/%{version}-%{release}/ || true
%endif


%if %{?use_pipewire_camera}
echo 'pref("media.webrtc.camera.allow-pipewire", true);' >> %{buildroot}%{mozappdir}/defaults/preferences/all-redhat.js
%endif

# Add distribution.ini
%{__mkdir_p} %{buildroot}%{mozappdir}/distribution
%{__sed} -e "s/__NAME__/%(source /etc/os-release; echo ${NAME})/g" \
         -e "s/__ID__/%(source /etc/os-release; echo ${ID})/g" \
         -e "s/rhel/redhat/g" \
         -e "s/Fedora.*/Fedora/g" \
         %{SOURCE26} > %{buildroot}%{mozappdir}/distribution/distribution.ini

# Install appdata file
mkdir -p %{buildroot}%{_datadir}/metainfo
%{__sed} -e "s/__VERSION__/%{version}/" \
         -e "s/__DATE__/$(date '+%Y-%m-%d')/" \
         %{SOURCE33} > %{buildroot}%{_datadir}/metainfo/firefox.appdata.xml

# Install Gnome search provider files
mkdir -p %{buildroot}%{_datadir}/gnome-shell/search-providers
%{__cp} %{SOURCE34} %{buildroot}%{_datadir}/gnome-shell/search-providers

# Remove gtk2 support as flash plugin is no longer supported
rm -rf %{buildroot}%{mozappdir}/gtk2/

# Create a symlink to replace libnssckbi.so with p11-kit-client.so
# instead of p11-kit-trust.so, so that Firefox can see the system
# trust store on the host through the p11-kit RPC protocol.  A symlink
# to libnss3.so is also needed, because Firefox tries to load
# libnssckbi.so from the same directory where libnss3.so is loaded (as
# of Firefox 89).
%if 0%{?flatpak}
ln -sf /usr/lib64/libnss3.so %{buildroot}%{_libdir}/libnss3.so
ln -sf /usr/lib64/pkcs11/p11-kit-client.so %{buildroot}%{_libdir}/libnssckbi.so
%endif

# clean the created bundled rpms if there are any
rm -rf %{_srcrpmdir}/libffi*.src.rpm
find %{_rpmdir} -name "libffi*.rpm" -delete
rm -rf %{_srcrpmdir}/openssl*.src.rpm
find %{_rpmdir} -name "openssl*.rpm" -delete
rm -rf %{_srcrpmdir}/nss*.src.rpm
find %{_rpmdir} -name "nss*.rpm" -delete
rm -rf %{_srcrpmdir}/nspr*.src.rpm
find %{_rpmdir} -name "nspr*.rpm" -delete

#---------------------------------------------------------------------

%check
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/*.appdata.xml

%preun
# is it a final removal?
if [ $1 -eq 0 ]; then
  %{__rm} -rf %{mozappdir}/components
  %{__rm} -rf %{mozappdir}/extensions
  %{__rm} -rf %{mozappdir}/plugins
fi

%post
update-desktop-database &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
update-desktop-database &> /dev/null || :
if [ $1 -eq 0 ] ; then
    touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
    %{__rm} -rf %{langpackdir}
fi

%posttrans
gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files -f %{name}.lang
%{_bindir}/firefox
%{mozappdir}/firefox
%{mozappdir}/firefox-bin
%doc %{_mandir}/man1/*
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/*
%dir %{_datadir}/mozilla/extensions/*
%dir %{_libdir}/mozilla/extensions/*
%{_datadir}/applications/%{name}.desktop
%{_datadir}/metainfo/*.appdata.xml
%{_datadir}/gnome-shell/search-providers/*.ini
%dir %{mozappdir}
%license %{mozappdir}/LICENSE
%{mozappdir}/browser/chrome
%{mozappdir}/defaults/preferences/*
%{mozappdir}/browser/defaults/preferences
#%{mozappdir}/browser/features/*.xpi
%{mozappdir}/distribution/distribution.ini
# That's Windows only
%ghost %{mozappdir}/browser/features/aushelper@mozilla.org.xpi
%if %{with langpacks}
%dir %{langpackdir}
%endif
%{mozappdir}/browser/omni.ja
%{mozappdir}/application.ini
%{mozappdir}/pingsender
%exclude %{mozappdir}/removed-files
%if 0%{?flatpak}
%{_libdir}/libnss3.so
%{_libdir}/libnssckbi.so
%endif
%{_datadir}/icons/hicolor/16x16/apps/firefox.png
%{_datadir}/icons/hicolor/22x22/apps/firefox.png
%{_datadir}/icons/hicolor/24x24/apps/firefox.png
%{_datadir}/icons/hicolor/256x256/apps/firefox.png
%{_datadir}/icons/hicolor/32x32/apps/firefox.png
%{_datadir}/icons/hicolor/48x48/apps/firefox.png
%{_datadir}/icons/hicolor/symbolic/apps/firefox-symbolic.svg
%{mozappdir}/*.so
%{mozappdir}/defaults/pref/channel-prefs.js
%{mozappdir}/dependentlibs.list
%{mozappdir}/dictionaries
%{mozappdir}/omni.ja
%{mozappdir}/platform.ini
%{mozappdir}/gmp-clearkey
%{mozappdir}/fonts/TwemojiMozilla.ttf
%{mozappdir}/glxtest
%{mozappdir}/vaapitest
%ifarch aarch64 riscv64
%{mozappdir}/v4l2test
%endif

%if !%{?system_nss}
#%exclude %{mozappdir}/libnssckbi.so
%endif

%if 0%{?bundle_nss}
%{mozappdir}/bundled/%{_lib}/libfreebl*
%{mozappdir}/bundled/%{_lib}/libnss*
%{mozappdir}/bundled/%{_lib}/libsmime3*
%{mozappdir}/bundled/%{_lib}/libsoftokn*
%{mozappdir}/bundled/%{_lib}/libssl3*
%{mozappdir}/bundled/%{_lib}/libnspr4.so
%{mozappdir}/bundled/%{_lib}/libplc4.so
%{mozappdir}/bundled/%{_lib}/libplds4.so
%endif

#---------------------------------------------------------------------

%changelog
* Fri Nov  7 2025 Jan Horak <jhorak@redhat.com> - 140.5.0-2
- Update to 140.5.0 ESR

* Fri Oct 10 2025 Jan Horak <jhorak@redhat.com> - 140.4.0-3
- Update to 140.4.0 ESR

* Wed Sep 10 2025 Jan Horak <jhorak@redhat.com> - 140.3.0-1
- Update to 140.3.0

* Fri Aug 15 2025 Jan Grulich <jgrulich@redhat.com> - 128.14.0-2
- Add missing translations

* Tue Aug 12 2025 Jan Grulich <jgrulich@redhat.com> - 128.14.0-1
- Update to 128.14.0 build1

* Tue Jul 15 2025 Eike Rathke <erack@redhat.com> - 128.13.0-1
- Update to 128.13.0 build1

* Tue Jun 17 2025 Eike Rathke <erack@redhat.com> - 128.12.0-1
- Update to 128.12.0 build1

* Wed May 21 2025 Eike Rathke <erack@redhat.com> - 128.11.0-1
- Update to 128.11.0

* Mon May 19 2025 Eike Rathke <erack@redhat.com> - 128.10.1-1
- Update to 128.10.1

* Tue Apr 22 2025 Eike Rathke <erack@redhat.com> - 128.10.0-1
- Update to 128.10.0 build1

* Mon Apr 14 2025 Eike Rathke <erack@redhat.com> - 128.9.0-3
- Bump NVR to rebuild for rhel-10.0.z

* Mon Mar 31 2025 Eike Rathke <erack@redhat.com> - 128.9.0-2
- Update to 128.9.0 build2

* Tue Mar 25 2025 Eike Rathke <erack@redhat.com> - 128.9.0-1
- Update to 128.9.0 build1

* Tue Mar 25 2025 Eike Rathke <erack@redhat.com> - 128.8.0-2
- Bump NVR for rebuild

* Mon Feb 24 2025 Eike Rathke <erack@redhat.com> - 128.8.0-1
- Update to 128.8.0 build1

* Tue Jan 28 2025 Eike Rathke <erack@redhat.com> - 128.7.0-1
- Update to 128.7.0 build1

* Wed Dec 18 2024 Eike Rathke <erack@redhat.com> - 128.6.0-1
- Update to 128.6.0 build1

* Mon Dec 02 2024 Eike Rathke <erack@redhat.com> - 128.5.1-1
- Update to 128.5.1

* Tue Nov 19 2024 Eike Rathke <erack@redhat.com> - 128.5.0-1
- Update to 128.5.0 build1

* Mon Nov 18 2024 Jan Grulich <jgrulich@redhat.com - 128.4.0-2
- Enable PipeWire camera support for RHEL 10
  + backport upstream fixes for PipeWire camera support
  Resolves: RHEL-64749

* Tue Oct 22 2024 Eike Rathke <erack@redhat.com> - 128.4.0-1
- Update to 128.4.0 build1

* Wed Oct 09 2024 Jan Horak <jhorak@redhat.com> - 128.3.1-1
- Update to 128.3.1

* Tue Sep 24 2024 Jan Horak <jhorak@redhat.com> - 128.3.0-1
- Update to 128.3.0

* Tue Aug 27 2024 Jan Horak <jhorak@redhat.com> - 128.2.0-1
- Update to 128.2.0

* Tue Apr 09 2024 Eike Rathke <erack@redhat.com> - 115.10.0-1
- Update to 115.10.0 build1

* Tue Apr 09 2024 Jan Horak <jhorak@redhat.com> - 115.9.1-2
- Removed expat CVE fix

* Fri Mar 22 2024 Eike Rathke <erack@redhat.com> - 115.9.1-1
- Update to 115.9.1

* Fri Mar 15 2024 Eike Rathke <erack@redhat.com> - 115.9.0-2
- Update to 115.9.0 build2

* Tue Mar 12 2024 Eike Rathke <erack@redhat.com> - 115.9.0-1
- Update to 115.9.0 build1
- Fix expat CVE-2023-52425

* Tue Feb 13 2024 Eike Rathke <erack@redhat.com> - 115.8.0-1
- Update to 115.8.0 build1

* Tue Jan 16 2024 Eike Rathke <erack@redhat.com> - 115.7.0-1
- Update to 115.7.0 build1

* Tue Dec 12 2023 Eike Rathke <erack@redhat.com> - 115.6.0-1
- Update to 115.6.0 build1

* Tue Nov 14 2023 Eike Rathke <erack@redhat.com> - 115.5.0-1
- Update to 115.5.0 build1

* Tue Oct 17 2023 Eike Rathke <erack@redhat.com> - 115.4.0-1
- Update to 115.4.0 build1
- Add fix for CVE-2023-44488
- Set homepage from os-release HOME_URL

* Fri Sep 29 2023 Eike Rathke <erack@redhat.com> - 115.3.1-1
- Update to 115.3.1

* Thu Sep 21 2023 Jan Horak <jhorak@redhat.com> - 115.3.0-1
- Update to 115.3.0 ESR

* Mon Sep  4 2023 Jan Horak <jhorak@redhat.com> - 115.2.0-3
- Update to 115.2.0 ESR

* Wed Aug  2 2023 Jan Horak <jhorak@redhat.com> - 115.1.0-1
- Update to 115.1.0 ESR

* Mon Jul 17 2023 Jan Horak <jhorak@redhat.com> - 115.0.2-1
- Update to 115.0.2 ESR

* Wed Jun 21 2023 Jan Horak <jhorak@redhat.com> - 115.0b8-1
- Update to 115.0b8

* Thu May 04 2023 Eike Rathke <erack@redhat.com> - 102.11.0-2
- Update to 102.11.0 build2

* Tue May 02 2023 Eike Rathke <erack@redhat.com> - 102.11.0-1
- Update to 102.11.0 build1

* Tue Apr 04 2023 Eike Rathke <erack@redhat.com> - 102.10.0-1
- Update to 102.10.0 build1

* Fri Mar 10 2023 Eike Rathke <erack@redhat.com> - 102.9.0-4
- Update to 102.9.0 build2

* Thu Mar 09 2023 Jan Horak <jhorak@redhat.com> - 102.9.0-2
- removed disable-openh264-download

* Tue Mar 07 2023 Eike Rathke <erack@redhat.com> - 102.9.0-1
- Update to 102.9.0 build1

* Tue Feb 14 2023 Eike Rathke <erack@redhat.com> - 102.8.0-2
- Update to 102.8.0 build2

* Tue Feb 07 2023 Eike Rathke <erack@redhat.com> - 102.8.0-1
- Update to 102.8.0 build1

* Tue Jan 10 2023 Eike Rathke <erack@redhat.com> - 102.7.0-1
- Update to 102.7.0 build1

* Mon Jan 02 2023 Jan Horak <jhorak@redhat.com> - 102.6.0-2
- Add firefox-x11 subpackage to allow explicit run of firefox under x11 on RHEL9

* Tue Dec 06 2022 Eike Rathke <erack@redhat.com> - 102.6.0-1
- Update to 102.6.0 build1

* Fri Nov 25 2022 Jan Horak <jhorak@redhat.com> - 102.5.0-2
- Added libwebrtc screencast patch for newer features

* Wed Nov 09 2022 Eike Rathke <erack@redhat.com> - 102.5.0-1
- Update to 102.5.0 build1

* Wed Oct 12 2022 Eike Rathke <erack@redhat.com> - 102.4.0-1
- Update to 102.4.0 build1

* Tue Oct 11 2022 Jan Horak <jhorak@redhat.com> - 102.3.0-7
- Fix for expat CVE-2022-40674 and non functional webrtc

* Tue Sep 13 2022 Jan Horak <jhorak@redhat.com> - 102.3.0-6
- Update to 102.3.0 build1

* Thu Jul 21 2022 Eike Rathke <erack@redhat.com> - 91.12.0-1
- Update to 91.12.0 build1

* Thu Jun 23 2022 Eike Rathke <erack@redhat.com> - 91.11.0-2
- Update to 91.11.0 build2

* Tue Jun 21 2022 Eike Rathke <erack@redhat.com> - 91.11.0-1
- Update to 91.11.0 build1

* Tue May 24 2022 Eike Rathke <erack@redhat.com> - 91.10.0-1
- Update to 91.10.0 build1

* Fri May 20 2022 Jan Horak <jhorak@redhat.com> - 91.9.1-1
- Update to 91.9.1 build1

* Tue Apr 26 2022 Eike Rathke <erack@redhat.com> - 91.9.0-1
- Update to 91.9.0

* Tue Apr 05 2022 Eike Rathke <erack@redhat.com> - 91.8.0-1
- Update to 91.8.0

* Mon Mar 07 2022 Eike Rathke <erack@redhat.com> - 91.7.0-3
- Update to 91.7.0 build3

* Wed Mar 02 2022 Jan Horak <jhorak@redhat.com> - 91.7.0-2
- Added expat backports of CVE-2022-25235, CVE-2022-25236 and CVE-2022-25315

* Tue Mar 01 2022 Eike Rathke <erack@redhat.com> - 91.7.0-1
- Update to 91.7.0 build2

* Fri Feb 25 2022 Jan Horak <jhorak@redhat.com> - 91.6.0-2
- Install langpacks to the browser/extensions to make them available in UI:
  rhbz#2030190

* Wed Feb 02 2022 Eike Rathke <erack@redhat.com> - 91.6.0-1
- Update to 91.6.0 build1

* Wed Feb 02 2022 Jan Horak <jhorak@redhat.com> - 91.5.0-2
- Use default update channel to fix non working enterprise policies:
  rhbz#2044667

* Thu Jan 06 2022 Eike Rathke <erack@redhat.com> - 91.5.0-1
- Update to 91.5.0 build1

* Mon Dec 13 2021 Jan Horak <jhorak@redhat.com> - 91.4.0-2
- Added fix for failing addons signatures.

* Wed Dec 01 2021 Eike Rathke <erack@redhat.com> - 91.4.0-1
- Update to 91.4.0 build1

* Mon Nov 01 2021 Eike Rathke <erack@redhat.com> - 91.3.0-1
- Update to 91.3.0 build1

* Thu Oct 21 2021 Jan Horak <jhorak@redhat.com> - 91.2.0-5
- Fixed crashes when FIPS is enabled.

* Mon Oct 04 2021 Jan Horak <jhorak@redhat.com> - 91.2.0-4
- Disable webrender on the s390x due to wrong colors: rhbz#2009503

* Wed Sep 29 2021 Jan Horak <jhorak@redhat.com> - 91.2.0-3
- Update to 91.2.0 build1

* Wed Sep 15 2021 Jan Horak <jhorak@redhat.com> - 91.1.0-1
- Update to 91.1.0 build1

* Tue Aug 17 2021 Jan Horak <jhorak@redhat.com>
- Update to 91.0.1 build1

* Tue Aug 10 2021 Jan Horak <jhorak@redhat.com> - 91.0-1
- Update to 91.0 ESR

* Thu Jul 29 2021 Jan Horak <jhorak@redhat.com> - 91.0-1
- Update to 91.0b8

* Fri Jul 16 2021 Jan Horak <jhorak@redhat.com> - 78.12.0-2
- Rebuild to pickup older nss

* Wed Jul 07 2021 Eike Rathke <erack@redhat.com> - 78.12.0-1
- Update to 78.12.0 build1

* Mon May 31 2021 Eike Rathke <erack@redhat.com> - 78.11.0-3
- Update to 78.11.0 build2 (release)

* Thu May 27 2021 Eike Rathke <erack@redhat.com> - 78.11.0-2
- Fix rhel_minor_version for dist .el8_4 and .el8

* Tue May 25 2021 Eike Rathke <erack@redhat.com> - 78.11.0-1
- Update to 78.11.0 build1

* Tue Apr 20 2021 Eike Rathke <erack@redhat.com> - 78.10.0-1
- Update to 78.10.0

* Wed Mar 17 2021 Eike Rathke <erack@redhat.com> - 78.9.0-1
- Update to 78.9.0 build1

* Wed Feb 17 2021 Eike Rathke <erack@redhat.com> - 78.8.0-1
- Update to 78.8.0 build2

* Tue Feb 09 2021 Eike Rathke <erack@redhat.com> - 78.7.1-1
- Update to 78.7.1

* Tue Feb 09 2021 Jan Horak <jhorak@redhat.com> - 78.7.0-3
- Fixing install prefix for the homepage

* Fri Jan 22 2021 Eike Rathke <erack@redhat.com> - 78.7.0-2
- Update to 78.7.0 build2

* Wed Jan 20 2021 Eike Rathke <erack@redhat.com> - 78.7.0-1
- Update to 78.7.0 build1

* Wed Jan  6 2021 Eike Rathke <erack@redhat.com> - 78.6.1-1
- Update to 78.6.1 build1

* Thu Dec 10 2020 Jan Horak <jhorak@redhat.com> - 78.6.0-1
- Update to 78.6.0 build1

* Wed Nov 18 2020 Jan Horak <jhorak@redhat.com> - 78.5.0-1
- Update to 78.5.0 build1

* Tue Nov 10 2020 erack@redhat.com - 78.4.1-1
- Update to 78.4.1

* Tue Nov 10 2020 Jan Horak <jhorak@redhat.com> - 78.4.0-3
- Fixing flatpak build, fixing firefox.sh.in to not disable langpacks loading

* Thu Oct 29 2020 Jan Horak <jhorak@redhat.com> - 78.4.0-2
- Enable addon sideloading

* Fri Oct 16 2020 Jan Horak <jhorak@redhat.com> - 78.4.0-1
- Update to 78.4.0 build2

* Fri Sep 18 2020 Jan Horak <jhorak@redhat.com>
- Update to 78.3.0 build1

* Tue Aug 18 2020 Jan Horak <jhorak@redhat.com> - 78.2.0-3
- Update to 78.2.0 build1

* Fri Jul 24 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.11.0 build1

* Fri Jun 26 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.10.0 build1

* Fri May 29 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.9.0 build1
- Added patch for pipewire 0.3

* Mon May 11 2020 Jan Horak <jhorak@redhat.com>
- Added s390x specific patches

* Wed Apr 29 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.8.0 build1

* Thu Apr 23 2020 Martin Stransky <stransky@redhat.com> - 68.7.0-3
- Added fix for rhbz#1821418

* Tue Apr 07 2020 Jan Horak <jhorak@redhat.com> - 68.7.0-2
- Update to 68.7.0 build3

* Mon Apr  6 2020 Jan Horak <jhorak@redhat.com> - 68.6.1-1
- Update to 68.6.1 ESR

* Wed Mar 04 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.6.0 build1

* Mon Feb 24 2020 Martin Stransky <stransky@redhat.com> - 68.5.0-3
- Added fix for rhbz#1805667
- Enabled mzbz@1170092 - Firefox prefs at /etc

* Fri Feb 07 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.5.0 build2

* Wed Feb 05 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.5.0 build1

* Wed Jan 08 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.4.1esr build1

* Fri Jan 03 2020 Jan Horak <jhorak@redhat.com>
- Update to 68.4.0esr build1

* Wed Dec 18 2019 Jan Horak <jhorak@redhat.com>
- Fix for wrong intl.accept_lang when using non en-us langpack

* Wed Nov 27 2019 Martin Stransky <stransky@redhat.com> - 68.3.0-1
- Update to 68.3.0 ESR

* Thu Oct 24 2019 Martin Stransky <stransky@redhat.com> - 68.2.0-4
- Added patch for TLS 1.3 support.

* Wed Oct 23 2019 Martin Stransky <stransky@redhat.com> - 68.2.0-3
- Rebuild

* Mon Oct 21 2019 Martin Stransky <stransky@redhat.com> - 68.2.0-2
- Rebuild

* Thu Oct 17 2019 Martin Stransky <stransky@redhat.com> - 68.2.0-1
- Update to 68.2.0 ESR

* Thu Oct 10 2019 Martin Stransky <stransky@redhat.com> - 68.1.0-6
- Enable system nss on RHEL6

* Thu Sep  5 2019 Jan Horak <jhorak@redhat.com> - 68.1.0-2
- Enable building langpacks

* Wed Aug 28 2019 Jan Horak <jhorak@redhat.com> - 68.1.0-1
- Update to 68.1.0 ESR

* Mon Aug 5 2019 Martin Stransky <stransky@redhat.com> - 68.0.1-4
- Enable system nss

* Mon Jul 29 2019 Martin Stransky <stransky@redhat.com> - 68.0.1-3
- Enable official branding

* Fri Jul 26 2019 Martin Stransky <stransky@redhat.com> - 68.0.1-2
- Enabled PipeWire on RHEL8

* Fri Jul 26 2019 Martin Stransky <stransky@redhat.com> - 68.0.1-1
- Updated to 68.0.1 ESR

* Tue Jul 16 2019 Jan Horak <jhorak@redhat.com> - 68.0-0.11
- Update to 68.0 ESR

* Tue Jun 25 2019 Martin Stransky <stransky@redhat.com> - 68.0-0.10
- Updated to 68.0 alpha 13
- Enabled second arches

* Fri Mar 22 2019 Martin Stransky <stransky@redhat.com> - 68.0-0.1
- Updated to 68.0 alpha

* Fri Mar 15 2019 Martin Stransky <stransky@redhat.com> - 60.6.0-3
- Added Google API keys (mozbz#1531176)

* Thu Mar 14 2019 Martin Stransky <stransky@redhat.com> - 60.6.0-2
- Update to 60.6.0 ESR (Build 2)

* Wed Mar 13 2019 Martin Stransky <stransky@redhat.com> - 60.6.0-1
- Update to 60.6.0 ESR (Build 1)

* Wed Feb 13 2019 Jan Horak <jhorak@redhat.com> - 60.5.1-1
- Update to 60.5.1 ESR

* Wed Feb 6 2019 Martin Stransky <stransky@redhat.com> - 60.5.0-3
- Added fix for rhbz#1672424 - Firefox crashes on NFS drives.

* Fri Jan 25 2019 Martin Stransky <stransky@redhat.com> - 60.5.0-2
- Updated to 60.5.0 ESR build2

* Tue Jan 22 2019 Martin Stransky <stransky@redhat.com> - 60.5.0-1
- Updated to 60.5.0 ESR build1

* Thu Jan 10 2019 Jan Horak <jhorak@redhat.com> - 60.4.0-3
- Fixing fontconfig warnings (rhbz#1601475)

* Wed Jan  9 2019 Jan Horak <jhorak@redhat.com> - 60.4.0-2
- Added pipewire patch from Tomas Popela (rhbz#1664270)

* Wed Dec  5 2018 Jan Horak <jhorak@redhat.com> - 60.4.0-1
- Update to 60.4.0 ESR

* Tue Dec  4 2018 Jan Horak <jhorak@redhat.com> - 60.3.0-2
- Added firefox-gnome-shell-extension

* Fri Oct 19 2018 Jan Horak <jhorak@redhat.com> - 60.3.0-1
- Update to 60.3.0 ESR

* Wed Oct 10 2018 Jan Horak <jhorak@redhat.com> - 60.2.2-2
- Added patch for rhbz#1633932

* Tue Oct  2 2018 Jan Horak <jhorak@redhat.com> - 60.2.2-1
- Update to 60.2.2 ESR

* Mon Sep 24 2018 Jan Horak <jhorak@redhat.com> - 60.2.1-1
- Update to 60.2.1 ESR

* Fri Aug 31 2018 Jan Horak <jhorak@redhat.com> - 60.2.0-1
- Update to 60.2.0 ESR

* Tue Aug 28 2018 Jan Horak <jhorak@redhat.com> - 60.1.0-9
- Do not set user agent (rhbz#1608065)
- GTK dialogs are localized now (rhbz#1619373)
- JNLP association works again (rhbz#1607457)

* Thu Aug 16 2018 Jan Horak <jhorak@redhat.com> - 60.1.0-8
- Fixed homepage and bookmarks (rhbz#1606778)
- Fixed missing file associations in RHEL6 (rhbz#1613565)

* Thu Jul 12 2018 Jan Horak <jhorak@redhat.com> - 60.1.0-7
- Run at-spi-bus if not running already (for the bundled gtk3)

* Mon Jul  9 2018 Jan Horak <jhorak@redhat.com> - 60.1.0-6
- Fix for missing schemes for bundled gtk3

* Mon Jun 25 2018 Martin Stransky <stransky@redhat.com> - 60.1.0-5
- Added mesa-libEGL dependency to gtk3/rhel6

* Sun Jun 24 2018 Martin Stransky <stransky@redhat.com> - 60.1.0-4
- Disabled jemalloc on all second arches

* Fri Jun 22 2018 Martin Stransky <stransky@redhat.com> - 60.1.0-3
- Updated to 60.1.0 ESR build2

* Thu Jun 21 2018 Martin Stransky <stransky@redhat.com> - 60.1.0-2
- Disabled jemalloc on second arches

* Wed Jun 20 2018 Martin Stransky <stransky@redhat.com> - 60.1.0-1
- Updated to 60.1.0 ESR

* Wed Jun 13 2018 Jan Horak <jhorak@redhat.com> - 60.0-12
- Fixing bundled libffi issues
- Readded some requirements

* Mon Jun 11 2018 Martin Stransky <stransky@redhat.com> - 60.0-10
- Added fix for mozilla BZ#1436242 - IPC crashes.

* Mon Jun 11 2018 Jan Horak <jhorak@redhat.com> - 60.0-9
- Bundling libffi for the sec-arches
- Added openssl-devel for the Python
- Fixing bundled gtk3

* Fri May 18 2018 Martin Stransky <stransky@redhat.com> - 60.0-8
- Added fix for mozilla BZ#1458492

* Wed May 16 2018 Martin Stransky <stransky@redhat.com> - 60.0-7
- Added patch from rhbz#1498561 to fix ppc64(le) crashes.

* Wed May 16 2018 Martin Stransky <stransky@redhat.com> - 60.0-6
- Disabled jemalloc on second arches

* Sun May  6 2018 Jan Horak <jhorak@redhat.com> - 60.0-4
- Update to 60.0 ESR

* Thu Mar  8 2018 Jan Horak <jhorak@redhat.com> - 52.7.0-1
- Update to 52.7.0 ESR

* Mon Jan 29 2018 Martin Stransky <stransky@redhat.com> - 52.6.0-2
- Build Firefox for desktop arches only (x86_64 and ppc64le)

* Thu Jan 18 2018 Martin Stransky <stransky@redhat.com> - 52.6.0-1
- Update to 52.6.0 ESR

* Thu Nov  9 2017 Jan Horak <jhorak@redhat.com> - 52.5.0-1
- Update to 52.5.0 ESR

* Mon Sep 25 2017 Jan Horak <jhorak@redhat.com> - 52.4.0-1
- Update to 52.4.0 ESR

* Thu Aug  3 2017 Jan Horak <jhorak@redhat.com> - 52.3.0-3
- Update to 52.3.0 ESR (b2)
- Require correct nss version

* Tue Jun 13 2017 Jan Horak <jhorak@redhat.com> - 52.2.0-1
- Update to 52.2.0 ESR

* Wed May 24 2017 Jan Horak <jhorak@redhat.com> - 52.1.2-1
- Update to 52.1.2 ESR

* Wed May 24 2017 Jan Horak <jhorak@redhat.com> - 52.0-7
- Added fix for accept language (rhbz#1454322)

* Wed Mar 22 2017 Jan Horak <jhorak@redhat.com> - 52.0-6
- Removing patch required for older NSS from RHEL 7.3
- Added patch for rhbz#1414564

* Fri Mar 17 2017 Martin Stransky <stransky@redhat.com> - 52.0-5
- Added fix for mozbz#1348168/CVE-2017-5428

* Mon Mar  6 2017 Jan Horak <jhorak@redhat.com> - 52.0-4
- Update to 52.0 ESR (b4)

* Thu Mar 2 2017 Martin Stransky <stransky@redhat.com> - 52.0-3
- Added fix for rhbz#1423012 - ppc64 gfx crashes

* Wed Mar  1 2017 Jan Horak <jhorak@redhat.com> - 52.0-2
- Enable system nss

* Tue Feb 28 2017 Martin Stransky <stransky@redhat.com> - 52.0-1
- Update to 52.0ESR (B1)
- Build RHEL7 package for Gtk3

* Mon Feb 27 2017 Martin Stransky <stransky@redhat.com> - 52.0-0.13
- Added fix for rhbz#1414535

* Tue Feb 21 2017 Jan Horak <jhorak@redhat.com> - 52.0-0.12
- Update to 52.0b8

* Tue Feb  7 2017 Jan Horak <jhorak@redhat.com> - 52.0-0.11
- Readded addons patch

* Mon Feb  6 2017 Jan Horak <jhorak@redhat.com> - 52.0-0.10
- Update to 52.0b3

* Tue Jan 31 2017 Jan Horak <jhorak@redhat.com> - 52.0-0.9
- Update to 52.0b2

* Fri Jan 27 2017 Jan Horak <jhorak@redhat.com> - 52.0-0.8
- Update to 52.0b1

* Thu Dec  8 2016 Jan Horak <jhorak@redhat.com> - 52.0-0.5
- Firefox Aurora 52 testing build

