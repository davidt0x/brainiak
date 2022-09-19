from distutils import sysconfig

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import site
import sys
import setuptools
from copy import deepcopy

assert sys.version_info >= (3, 5), (
    "Please use Python version 3.5 or higher, "
    "lower versions are not supported"
)

# https://github.com/pypa/pip/issues/7953#issuecomment-645133255
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

ext_modules = [
    Extension(
        'brainiak.factoranalysis.tfa_extension',
        ['brainiak/factoranalysis/tfa_extension.cpp'],
    ),
    Extension(
        'brainiak.fcma.fcma_extension',
        ['brainiak/fcma/src/fcma_extension.cc'],
    ),
    Extension(
        'brainiak.fcma.cython_blas',
        ['brainiak/fcma/cython_blas.pyx'],
    ),
    Extension(
        'brainiak.eventseg._utils',
        ['brainiak/eventseg/_utils.pyx'],
    ),
]


# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.

    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'unix': ['-g0', '-fopenmp'],
    }

    # FIXME Workaround for using the Intel compiler by setting the CC env var
    # Other uses of ICC (e.g., cc binary linked to icc) are not supported
    if (('CC' in os.environ and 'icc' in os.environ['CC'])
            or (sysconfig.get_config_var('CC') and 'icc' in sysconfig.get_config_var('CC'))):
        c_opts['unix'] += ['-lirc', '-lintlc']

    if sys.platform == 'darwin':
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.9',
                           '-ftemplate-depth-1024']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' %
                        self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = deepcopy(opts)
            ext.extra_link_args = deepcopy(opts)
            lang = ext.language or self.compiler.detect_language(ext.sources)
            if lang == 'c++':
                ext.extra_compile_args.append(cpp_flag(self.compiler))
                ext.extra_link_args.append(cpp_flag(self.compiler))
        build_ext.build_extensions(self)

    def finalize_options(self):
        super().finalize_options()
        import numpy
        import pybind11
        self.include_dirs.extend([
            numpy.get_include(),
            pybind11.get_include(user=True),
            pybind11.get_include(),
        ])


extras = {
    "dev": [
		"pytest",
		"coverage",
		"flake8",
		"flake8-print",
		"mypy",
		"myst-nb",
		"restructuredtext-lint",
		"setuptools_scm",
		"sphinx",
		"sphinx_rtd_theme",
		"towncrier",
		"numdifftools",
		"testbook"
	],

	'matnormal': [
            'tensorflow',
            'tensorflow_probability<=0.15.0',
        ],

	# All requirements for notebook examples in docs/examples
    "examples": [
		"nilearn",
		"nxviz<=0.6.3",
		"nltools",
		"timecorr",
		"seaborn",
		"holoviews",
		"pyOpenSSL",
		"awscli",
		"bcrypt",
		"indexed_gzip",
		"inflect",
		"ipython",
		"jupyter",
                "mypy @ git+https://github.com/python/mypy.git",
		"nibabel",
		"nilearn",
		"nodejs",
		"numpy",
		"pydicom",
		"requests",
		"rpyc",
		"scikit-learn",
		"scipy",
		"toml",
		"tornado",
		"websocket-client",
		"wsaccel",
		"inotify",
		"pybids",
		"watchdog"
	],
}
extras["all"] = sum(extras.values(), [])


setup(
    extras_require=extras,
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
)
