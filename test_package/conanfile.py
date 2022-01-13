from conans import ConanFile, CMake, tools, RunEnvironment
from subprocess import Popen, PIPE
import os
import tempfile


class cycloneddsCxxTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = ("cmake_paths", "cmake_find_package")
    _cmake = None

    def _configure_cmake(self):
        if self._cmake is None:
            self._cmake = CMake(self)
            cmake = self._cmake
            cmake.configure()
        return self._cmake

    def build(self):
        if not tools.cross_building(self):
            cmake = self._configure_cmake()
            cmake.build()

    def test(self):
        if tools.cross_building(self.settings):
            print("NOT RUN (cross-building)")
            return

        env_build = RunEnvironment(self)

        with tools.environment_append(env_build.vars):
            program1 = "ddscxxHelloworldSubscriber"
            program2 = "ddscxxHelloworldPublisher"
            if self.settings.os == "Windows":
                program1 += '.exe'
                program2 += '.exe'
                test_path = os.path.join(self.build_folder,
                                         str(self.settings.build_type))
            else:
                test_path = '.' + os.sep

            f1 = tempfile.TemporaryFile()
            f2 = tempfile.TemporaryFile()
            cmds_list = [(os.path.join(test_path, program1), f1),
                         (os.path.join(test_path, program2), f2)]
            procs_list = [Popen(cmd, stdout=f, stderr=PIPE) for (cmd, f) in cmds_list]
            for proc in procs_list:
                proc.wait()

            f1.seek(0)
            f2.seek(0)
            self.output.info(b'\n'.decode() + f1.read().decode() + b'\n'.decode() + f2.read().decode())
            f1.close()
            f2.close()
