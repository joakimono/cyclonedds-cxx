from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import subprocess
import sys

required_conan_version = ">=1.33.0"


class cycloneddsCxxConan(ConanFile):
    name = "cyclonedds-cxx"
    license = "EPL-2.0, EDL-1.0"
    author = "SINTEF Ocean"
    url = "https://github.com/sintef-ocean/conan-cyclonedds-cxx"
    homepage = "https://cyclonedds.io/"
    description = "C++ bindings for Eclipse Cyclone DDS " \
        " (Data Distribution Service) implementation " \
        "of the OMG (Object Management Group)."
    topics = ("c-plus-plus", "omg", "dds", "ros2", "middleware", "rtps")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "with_shm": [True, False],
        "with_ddslib": [True, False],
        "with_idllib": [True, False],
        "with_legacy": [True, False],
        "with_type_discovery": [True, False],
        "with_topic_discovery": [True, False],
        "with_doc": [True, False],
        "with_examples": [True, False],
        "with_tests": [True, False],
        "with_analyzer": [True, False, "clang-tidy"],
        "with_coverage": [True, False],
        "with_sanitizer": "ANY",
        "with_werror": [True, False],
        "iceoryx_posh_testing": "ANY"

    }
    default_options = {
        "shared": True,
        "with_shm": True,
        "with_ddslib": True,
        "with_idllib": True,
        "with_legacy": False,
        "with_type_discovery": True,
        "with_topic_discovery": True,
        "with_doc": False,
        "with_examples": False,
        "with_tests": False,
        "with_analyzer": False,
        "with_coverage": False,
        "with_sanitizer": "",
        "with_werror": False,  # Fail: ICO C forbids forward reference to 'enum'
        "iceoryx_posh_testing": ""  # Escape hatch for testing with_shm

    }
    generators = ("cmake", "cmake_paths", "cmake_find_package")
    exports_sources = ['patches/*']
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def requirements(self):
        _deps = self.conan_data["dependencies"][self.version]
        self.requires("cyclonedds/{}".format(_deps["cyclonedds"]))
        if self.options.get_safe("with_legacy", False):
            self.requires("boost/{}".format(_deps["boost"]))

    def build_requirements(self):
        _deps = self.conan_data["dependencies"][self.version]
        if self.options.with_doc:
            self.build_requires("doxygen/{}".format(_deps["doxygen"]))
        if self.options.with_tests:
            self.build_requires("gtest/{}".format(_deps["gtest"]))

    def config_options(self):
        if tools.Version(self.version) < "0.11.0":
            del self.options.with_ddslib
        if tools.Version(self.version) < "0.10.2":
            del self.options.with_idllib
            del self.options.with_legacy
            del self.options.with_type_discovery
            del self.options.with_topic_discovery

    def configure(self):
        self.options["cyclonedds"].with_shm = self.options.with_shm
        if tools.Version(self.version) >= "0.10.2":
            self.options["cyclonedds"].with_type_discovery = \
                self.options.with_type_discovery
            self.options["cyclonedds"].with_topic_discovery = \
                self.options.with_topic_discovery

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def _configure_cmake(self):
        if self._cmake is None:
            self._cmake = CMake(self)

            _defs = dict()

            _defs["CMAKE_BUILD_TYPE"] = self.settings.build_type
            _defs["ENABLE_SHM"] = self.options.with_shm
            if tools.Version(self.version) >= "0.10.2":
                _defs["ENABLE_LEGACY"] = self.options.with_legacy
                _defs["ENABLE_TYPE_DISCOVERY"] = self.options.with_type_discovery
                _defs["ENABLE_TOPIC_DISCOVERY"] = self.options.with_topic_discovery

            _defs["BUILD_DOCS"] = self.options.with_doc
            _defs["BUILD_EXAMPLES"] = self.options.with_examples
            _defs["BUILD_TESTING"] = self.options.with_tests

            if self.options.with_analyzer == 'clang-tidy':
                _defs["ANALYZER"] = self.options.with_analyzer
            elif self.options.with_analyzer is True:
                _defs["ANALYZER"] = 'ON'
            else:
                _defs["ANALYZER"] = 'OFF'
            _defs["ENABLE_COVERAGE"] = self.options.with_coverage
            _defs["SANITIZER"] = self.options.with_sanitizer
            _defs["WERROR"] = self.options.with_werror

            if self.options.iceoryx_posh_testing:
                # should be iceoryx install prefix + 'lib/cmake'
                self.output.info("Adding provided 'iceoryx_posh_testing'")
                _defs["CMAKE_PREFIX_PATH"] = self.options.iceoryx_posh_testing

            self._cmake.definitions.update(_defs)
            self._cmake.configure(source_folder=self._source_subfolder)
        return self._cmake

    def validate(self):
        if self.options.get_safe("with_legacy", False):
            tools.check_min_cppstd(self, "11")
        else:
            tools.check_min_cppstd(self, "17")
        if self.options.with_shm and not self.options["cyclonedds"].with_shm:
            raise ConanInvalidConfiguration(
                "For option 'with_shm=True', " +
                "options 'cyclonedds:with_shm' must be True too")

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

        if self.options.with_tests:
            cmake.parallel = False  # SharedMemoryTest fails with parallel
            cmake.test()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy('LICENSE', dst="licenses", src=self._source_subfolder,
                  ignore_case=True, keep_path=False)

    @property
    def _cyclonedds_components(self):
        def pthread():
            return ["pthread"] if self.settings.os in ["Linux", "FreeBSD"] else []

        def rt():
            return ["rt"] if self.settings.os in ["Linux", "FreeBSD"] else []

        def dl():
            return ["dl"] if self.settings.os in ["Linux", "FreeBSD"] else []

        def cyclonedds_ddsc():
            return ['cyclonedds::ddsc']

        def cyclonedds_idl():
            return ['cyclonedds::idl']

        def libcxx():
            libcxx = tools.stdcpp_library(self)
            return [libcxx] if libcxx and not self.options.shared else []

        def defs():
            return ["LEGACY_CXX"] if self.options.get_safe("with_legacy", False) else []

        _comps = dict()

        if self.options.get_safe("with_ddslib", True):
            _comps["ddscxx"] = {
                "target": "CycloneDDS::ddscxx",
                "type": "library",
                "lib_names": ['ddscxx'],
                "system_libs": pthread() + rt() + dl(),
                "requires": cyclonedds_ddsc(),
                "defines": defs(),
                "includedirs": ["include/ddscxx"],
            }

        if self.options.get_safe("with_idllib", True):
            _comps["idlcxx"] = {
                "target": "CycloneDDS::idlcxx",
                "type": "library",
                "lib_names": ['cycloneddsidlcxx'],
                "system_libs": pthread() + libcxx(),
                "requires": cyclonedds_idl(),
            }

        return _comps

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_subfolder,
                            "conan-official-{}-targets.cmake".format(self.name))

    def package_id(self):
        # The following options do not impact package id
        del self.info.options.with_tests
        del self.info.options.with_analyzer
        del self.info.options.with_coverage
        del self.info.options.with_sanitizer
        del self.info.options.with_werror
        del self.info.options.iceoryx_posh_testing

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "CycloneDDS-CXX"
        self.cpp_info.names["cmake_find_package_multi"] = "CycloneDDS-CXX"

        def _register_components(components):
            for cmake_lib_name, values in components.items():

                library = values.get("type", "not")
                if library != 'library':
                    continue
                system_libs = values.get("system_libs", [])
                lib_names = values.get("lib_names", [])
                requires = values.get("requires", [])
                defines = values.get("defines", [])
                includedirs = values.get("includedirs", [])

                self.cpp_info.components[cmake_lib_name].names["cmake_find_package"] = cmake_lib_name
                self.cpp_info.components[cmake_lib_name].names["cmake_find_package_multi"] = cmake_lib_name
                self.cpp_info.components[cmake_lib_name].includedirs = includedirs
                self.cpp_info.components[cmake_lib_name].libs = lib_names
                self.cpp_info.components[cmake_lib_name].defines = defines
                self.cpp_info.components[cmake_lib_name].system_libs = system_libs
                self.cpp_info.components[cmake_lib_name].requires = requires
                self.cpp_info.components[cmake_lib_name].builddirs.append(self._module_subfolder)
                if cmake_lib_name == 'idlcxx':
                    self.cpp_info.components[cmake_lib_name].build_modules["cmake_find_package"].append(
                        "lib/cmake/CycloneDDS-CXX/idlcxx/Generate.cmake")
                    self.cpp_info.components[cmake_lib_name].build_modules["cmake_find_package_multi"].append(
                        "lib/cmake/CycloneDDS-CXX/idlcxx/Generate.cmake")
        _register_components(self._cyclonedds_components)

    def system_requirements(self):
        if self.options.with_doc:
            self.output.info("Install python requirements for documentation")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                                   'Sphinx', 'breathe', 'exhale', 'sphinx-rtd-theme'])
