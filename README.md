[![GCC Conan](https://github.com/sintef-ocean/conan-cyclonedds-cxx/workflows/GCC%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-cyclonedds-cxx/actions?query=workflow%3A"GCC+Conan")
[![Clang Conan](https://github.com/sintef-ocean/conan-cyclonedds-cxx/workflows/Clang%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-cyclonedds-cxx/actions?query=workflow%3A"Clang+Conan")
[![MSVC Conan](https://github.com/sintef-ocean/conan-cyclonedds-cxx/workflows/MSVC%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-cyclonedds-cxx/actions?query=workflow%3A"MSVC+Conan")


[Conan.io](https://conan.io) recipe for [cyclonedds-cxx](https://cyclonedds.io/).

The package is usually consumed using the `conan install` command or a *conanfile.txt*.

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/en/latest/reference/commands/misc/remote.html?highlight=remotes):

   ```bash
   $ conan remote add sintef https://artifactory.smd.sintef.no/artifactory/api/conan/conan-local
   ```

2. Using *conanfile.txt* in your project with *cmake*

   Add a [*conanfile.txt*](http://docs.conan.io/en/latest/reference/conanfile_txt.html) to your project. This file describes dependencies and your configuration of choice, e.g.:

   ```
   [requires]
   cyclonedds-cxx/[>=0.8.2]@sintef/stable

   [options]
   None

   [imports]
   licenses, * -> ./licenses @ folder=True

   [generators]
   cmake_paths
   cmake_find_package
   ```

   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.13)
   project(TheProject CXX)

   include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
   find_package(CycloneDDS-CXX MODULE REQUIRED)
   #find_package(CycloneDDS-CXX CONFIG REQUIRED) # also available
   # idlcxx_generate function to create from idl is available

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor CycloneDDS-CXX::ddscxx)
   ```
   Then, do
   ```bash
   $ mkdir build && cd build
   $ conan install .. -s build_type=<build_type>
   ```
   where `<build_type>` is e.g. `Debug` or `Release`.
   You can now continue with the usual dance with cmake commands for configuration and compilation. For details on how to use conan, please consult [Conan.io docs](http://docs.conan.io/en/latest/)

## Package options

Option | Default | Domain
---|---|---
shared | [True, False] | True
with_shm | [True, False] | True
with_doc | [True, False] | False
with_examples | [True, False] | False
with_tests | [True, False] | False
with_analyzer | [True, False, "clang-tidy"] | False
with_coverage | [True, False] | False
with_sanitizer | ANY | ""
with_werror | [True, False] | False
iceoryx_posh_testing | ANY | ""

## Known recipe issues

conan-center's package iceoryx does not provide the target
`iceoryx_posh_roudi_environment`, (and `iceoryx_posh_testing::iceoryx_posh_testing`), so
`with_tests=True` and `with_shm=True` not work unless the missing packages are found by
CMake.  One workaround for this is to provide `CMAKE_PREFIX_PATH` using option
`iceoryx_posh_testing`, i.e. specifying the path to the library cmake config scripts (or
by installing iceoryx on a default search path).
