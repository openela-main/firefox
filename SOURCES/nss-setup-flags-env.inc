sed -i 's@%{bundled_install_path}@%{_buildrootdir}%{bundled_install_path}@g' %{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig/nss*.pc

export LDFLAGS="-L%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
export LDFLAGS="-Wl,-rpath,%{bundled_install_path}/%{_lib} $LDFLAGS"
export LDFLAGS="-Wl,-rpath-link,%{_buildrootdir}%{bundled_install_path}/%{_lib} $LDFLAGS"
export PKG_CONFIG_PATH=%{_buildrootdir}%{bundled_install_path}/%{_lib}/pkgconfig
export PATH="{_buildrootdir}%{bundled_install_path}/bin:$PATH"
