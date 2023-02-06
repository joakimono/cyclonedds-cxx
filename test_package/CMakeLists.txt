#
# Copyright(c) 2020 ADLINK Technology Limited and others
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v. 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
# v. 1.0 which is available at
# http://www.eclipse.org/org/documents/edl-v10.php.
#
# SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
#
project(helloworld LANGUAGES C CXX)
cmake_minimum_required(VERSION 3.5)

if(EXISTS "${CMAKE_BINARY_DIR}/conan_paths.cmake")
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
endif()

find_package(CycloneDDS-CXX MODULE REQUIRED)
#find_package(CycloneDDS-CXX CONFIG REQUIRED)

if(CycloneDDS-CXX_VERSION VERSION_LESS "0.10.2")
  set(_idl_file HelloWorldDataOld.idl_in)
else()
  set(_idl_file HelloWorldData.idl_in)
endif()
configure_file(${_idl_file} idls/HelloWorldData.idl)
idlcxx_generate(TARGET helloworlddata FILES "${CMAKE_CURRENT_BINARY_DIR}/idls/HelloWorldData.idl")

add_executable(ddscxxHelloworldPublisher publisher.cpp)
add_executable(ddscxxHelloworldSubscriber subscriber.cpp)

# Link both executables to idl data type library and ddscxx.
target_link_libraries(ddscxxHelloworldPublisher CycloneDDS-CXX::ddscxx helloworlddata)
target_link_libraries(ddscxxHelloworldSubscriber CycloneDDS-CXX::ddscxx helloworlddata)


get_target_property(cyclone_defs CycloneDDS-CXX::ddscxx INTERFACE_COMPILE_DEFINITIONS)
list(FIND cyclone_defs "LEGACY_CXX" _feature_idx)
if(_feature_idx GREATER -1)
  set_property(TARGET ddscxxHelloworldPublisher PROPERTY CXX_STANDARD 11)
  set_property(TARGET ddscxxHelloworldSubscriber PROPERTY CXX_STANDARD 11)
else()
  set_property(TARGET ddscxxHelloworldPublisher PROPERTY CXX_STANDARD 17)
  set_property(TARGET ddscxxHelloworldSubscriber PROPERTY CXX_STANDARD 17)
endif()
