%global specversion 5
%global upstream_version 0b41287

# Keep around for when/if required
#global alphatag #{upstream_version}.git

%global mh_release %{?alphatag:0.}%{specversion}%{?alphatag:.%{alphatag}}%{?dist}

Name:		matahari
Version:	0.4.0
Release:	%{mh_release}
Summary:	QMF Agents for Linux guests
Group:		Applications/System
License:	GPLv2
URL:		http://github.com/matahari/matahari/wiki

# wget --no-check-certificate -O matahari-{upstream_version}.tgz https://github.com/beekhof/matahari/tarball/{upstream_version}
Source0:	matahari-%{upstream_version}.tgz
Patch1:		matahari-2798d52.patch
Patch2:		matahari-0.4.1.patch
Patch3:		matahari-no-qpidd.patch
Patch4:		matahari-lsb.patch
Patch5:		matahari-qmf-lib.patch

ExclusiveArch:	i686 x86_64
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires:	dbus
Requires:	hal
Requires:	qmf > 0.7
Requires:	pcre
Requires:	%{name}-net = %{version}-%{release}
Requires:	%{name}-host = %{version}-%{release}
Requires:	%{name}-service = %{version}-%{release}

BuildRequires:	cmake
BuildRequires:	libudev-devel
BuildRequires:	gcc-c++
BuildRequires:	dbus-devel
BuildRequires:	hal-devel
BuildRequires:	qpid-cpp-client-devel > 0.7
BuildRequires:	qmf-devel > 0.7
BuildRequires:	pcre-devel
BuildRequires:	glib2-devel
BuildRequires:	sigar-devel

%description

Matahari provides QMF Agents that can be used to control and manage
various pieces of functionality, using the AMQP protocol.

The Advanced Message Queuing Protocol (AMQP) is an open standard application
layer protocol providing reliable transport of messages.

QMF provides a modeling framework layer on top of qpid (which implements
AMQP).  This interface allows you to manage a host and its various components
as a set of objects with properties and methods.

%package broker
License:	GPLv2+
Summary:	Optional AMQP Broker for Matahari
Group:		Applications/System
Requires:	%{name} = %{version}-%{release}
Requires:	qpid-cpp-server > 0.7
Requires:	qpid-cpp-server-ssl > 0.7
Requires:	qmf > 0.7

%description broker
Optional AMQP Broker for Matahari

%package lib
License:	GPLv2+
Summary:	C libraries used by Matahari agents
Group:		Applications/System

%description lib
C libraries used by Matahari agents

%package agent-lib
License:	GPLv2+
Summary:	C++ library used by Matahari agents
Group:		Applications/System
Requires:	%{name}-lib = %{version}-%{release}
Requires:	qpid-cpp-client-ssl > 0.7

%description agent-lib
C++ library containing the base class for Matahari agents

%package host
License:	GPLv2+
Summary:	QMF agent for remote hosts
Group:		Applications/System
Requires:	%{name}-lib = %{version}-%{release}
Requires:	%{name}-agent-lib = %{version}-%{release}

%description host
QMF agent for viewing and controlling remote hosts

%package net
License:	GPLv2+
Summary:	QMF agent for network devices  
Group:		Applications/System
Requires:	%{name}-lib = %{version}-%{release}
Requires:	%{name}-agent-lib = %{version}-%{release}

%description net
QMF agent for viewing and controlling network devices  

%package service
License:	GPLv2+
Summary:	QMF agent for system services
Group:		Applications/System
Requires:	%{name}-lib = %{version}-%{release}
Requires:	%{name}-agent-lib = %{version}-%{release}

%description service
QMF agent for viewing and controlling system services

%package devel
License:	GPLv2+
Summary:	Matahari development package
Group:		Development/Libraries
Requires:	%{name} = %{version}-%{release}
Requires:	%{name}-lib = %{version}-%{release}
Requires:	%{name}-agent-lib = %{version}-%{release}
Requires:	qpid-cpp-client-devel > 0.7
Requires:	qmf-devel > 0.7
Requires:	glib2-devel

%description devel
Headers and shared libraries for developing Matahari agents.

%prep
%setup -q -n beekhof-matahari-%{upstream_version}
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1

%build
%{cmake} -DCMAKE_BUILD_TYPE=RelWithDebInfo .
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%{__install} -d $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d
%{__install} matahari.init   $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/matahari-net
%{__install} matahari.init   $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/matahari-host
%{__install} matahari.init   $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/matahari-service
%{__install} matahari-broker $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/matahari-broker

%{__install} -d $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/
%{__install} matahari.sysconf $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/matahari
%{__install} matahari-broker.sysconf $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/matahari-broker
%{__ln_s} qpidd $RPM_BUILD_ROOT/%{_sbindir}/matahari-brokerd

%{__install} -d -m0755 %{buildroot}%{_localstatedir}/lib/%{name}
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/run/%{name}

%post -n matahari-lib -p /sbin/ldconfig
%postun -n matahari-lib -p /sbin/ldconfig

%post -n matahari-agent-lib -p /sbin/ldconfig
%postun -n matahari-agent-lib
# Can't use -p, gives: '/sbin/ldconfig: relative path `0' used to build cache' error
/sbin/ldconfig

#== Host

%post host
/sbin/service matahari-host condrestart

%preun host
if [ $1 = 0 ]; then
   /sbin/service matahari-host stop >/dev/null 2>&1 || :
   chkconfig --del matahari-host
fi

%postun host
if [ "$1" -ge "1" ]; then
    /sbin/service matahari-host condrestart >/dev/null 2>&1 || :
fi

#== Network

%post net
/sbin/service matahari-net condrestart

%preun net
if [ $1 = 0 ]; then
   /sbin/service matahari-net stop >/dev/null 2>&1 || :
   chkconfig --del matahari-net
fi

%postun net
if [ "$1" -ge "1" ]; then
    /sbin/service matahari-net condrestart >/dev/null 2>&1 || :
fi

#== Services

%post service
/sbin/service matahari-service condrestart

%preun service
if [ $1 = 0 ]; then
   /sbin/service matahari-service stop >/dev/null 2>&1 || :
   chkconfig --del matahari-service
fi

%postun service
if [ "$1" -ge "1" ]; then
    /sbin/service matahari-service condrestart >/dev/null 2>&1 || :
fi

#== Broker

%post broker
/sbin/service matahari-broker condrestart


%preun broker
if [ $1 = 0 ]; then
    /sbin/service matahari-broker stop >/dev/null 2>&1 || :
    chkconfig --del matahari-broker
fi

%postun broker
if [ "$1" -ge "1" ]; then
    /sbin/service matahari-broker condrestart >/dev/null 2>&1 || :
fi

%clean
test "x%{buildroot}" != "x" && rm -rf %{buildroot}

%files
%defattr(644, root, root, 755)
%doc AUTHORS COPYING

%files agent-lib
%defattr(644, root, root, 755)
%{_libdir}/libmqmfagent.so.*
%dir %{_datadir}/matahari/
%config(noreplace) %{_sysconfdir}/sysconfig/matahari
%doc AUTHORS COPYING

%files lib
%defattr(644, root, root, 755)
%{_libdir}/libmcommon.so.*
%{_libdir}/libmhost.so.*
%{_libdir}/libmnet.so.*
%{_libdir}/libmsrv.so.*
%doc AUTHORS COPYING

%files net
%defattr(644, root, root, 755)
%attr(755, root, root) %{_initddir}/matahari-net
%attr(755, root, root) %{_sbindir}/matahari-netd
%doc AUTHORS COPYING

%files host
%defattr(644, root, root, 755)
%attr(755, root, root) %{_initddir}/matahari-host
%attr(755, root, root) %{_sbindir}/matahari-hostd
%doc AUTHORS COPYING

%files service
%defattr(644, root, root, 755)
%attr(755, root, root) %{_initddir}/matahari-service
%attr(755, root, root) %{_sbindir}/matahari-serviced
%doc AUTHORS COPYING

%files broker
%defattr(644, root, root, 755)
%attr(755, root, root) %{_initddir}/matahari-broker
%config(noreplace) %{_sysconfdir}/sysconfig/matahari-broker
%config(noreplace) %{_sysconfdir}/matahari-broker.conf
%{_sbindir}/matahari-brokerd

%attr(755, qpidd, qpidd) %{_localstatedir}/lib/%{name}
%attr(755, qpidd, qpidd) %{_localstatedir}/run/%{name}
%doc AUTHORS COPYING

%files devel
%defattr(644, root, root, 755)
%{_datadir}/matahari/schema.xml
%{_includedir}/matahari.h
%{_libdir}/libm*.so
%doc AUTHORS COPYING

%changelog

* Wed Apr 20 2011 Andrew Beekhof <abeekhof@redhat.com> - 0.4.0-5
- Really do not start matahari services by default
- Resolves: rhbz#698370

* Wed Apr 20 2011 Andrew Beekhof <abeekhof@redhat.com> - 0.4.0-4
- Do not start matahari services by default
- Resolves: rhbz#698370

* Fri Apr 15 2011 Andrew Beekhof <abeekhof@redhat.com> - 0.4.0-3
- Add explicit dependancy on qpid-cpp-{client|server}-ssl
- Resolves: rhbz#696810

* Tue Apr  5 2011 Andrew Beekhof <abeekhof@redhat.com> - 0.4.0-2
- Add explicit versioned dependancies between relevant sub-packages
- Avoid the -libs package depending on QMF libraries
- Fix post and postun scripts for matahari-service
- Resolves: rhbz#688164 rhbz#692400 rhbz#688197 
- Resolves: rhbz#674185 rhbz#690587

* Thu Mar 24 2011 Andrew Beekhof <abeekhof@redhat.com> - 0.4.0-1
- Split the packaging up, one subpackage per agent 
- Remove dependancy on qpid-cpp-server-devel
- Convert agents to the QMFv2 API
- Rebuild for updated qpid-cpp
  Related: rhbz#658828

* Fri Feb  4 2011 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.30.0b41287.git
- Rebuild for updated qpid-cpp
  Related: rhbz#658828

* Fri Feb  4 2011 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.29.0b41287.git
- Update to upstream version 2798d52.git
  + Support password authentication to qpid
  + Prevent errors when matahari is started at boot
  Related: rhbz#658828

* Thu Jan 13 2011 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.28.0b41287.git
- Refresh from upstream
- Local broker is now optional
- Functional Host, Network and Services (including support for OCF Resources) agents
  Related: rhbz#658828
 
* Tue Jan 11 2011 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.27.ad8b81b.git
- Only build on Intel architectures for now due to qpid dependancy
  Related: rhbz#658828 

* Tue Jan 11 2011 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.26.ad8b81b.git
- Import into RHEL

* Wed Oct 12 2010 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.8.ad8b81b.git
- Added the Network agent
- Removed unnecessary OO-ness from existing Host agent/schema

* Fri Oct 01 2010 Adam Stokes <astokes@fedoraproject.org> - 0.4.0-0.1.5e26232.git
- Add schema-net for network api

* Tue Sep 21 2010 Andrew Beekhof <andrew@beekhof.net> - 0.4.0-0.1.9fc30e4.git
- Pre-release of the new cross platform version of Matahari
- Add matahari broker scripts

* Thu Oct 08 2009 Arjun Roy <arroy@redhat.com> - 0.0.4-7
- Refactored for new version of qpidc.

* Fri Oct 02 2009 Kevin Kofler <Kevin@tigcc.ticalc.org> - 0.0.4-6
- Rebuild for new qpidc.

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.4-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 16 2009 Arjun Roy <arroy@redhat.com> - 0.0.4-4
- Changed buildroot value to meet fedora packaging guidelines
- Updated project website

* Mon Jul 13 2009 Arjun Roy <arroy@redhat.com> - 0.0.4-3
- Quietened rpmlint errors and warnings.
- Fixed most gcc warnings.
- Changed init script so it doesn't run by default
- Now rpm specfile makes it so service runs by default instead

* Thu Jul 9 2009 Arjun Roy <arroy@redhat.com> - 0.0.4-2
- Bumped qpidc and qmf version requirements to 0.5.790661.

* Thu Jul 9 2009 Arjun Roy <arroy@redhat.com> - 0.0.4-1
- Removed dependency on boost. Added dependency on pcre.

* Thu Jul 2 2009 Arjun Roy <arroy@redhat.com> - 0.0.3-2
- Fixed bug with not publishing host hypervisor and arch to broker
- Updated aclocal.m4 to match new version of automake

* Tue Jun 30 2009 Arjun Roy <arroy@redhat.com> - 0.0.3-1
- Added getopt and daemonize support
- Added sysV init script support

* Mon Jun 29 2009 Arjun Roy <arroy@redhat.com> - 0.0.2-1
- Now tracks hypervisor and arch using libvirt

* Tue Jun 23 2009 Arjun Roy <arroy@redhat.com> - 0.0.1-1
- Initial rpmspec packaging
