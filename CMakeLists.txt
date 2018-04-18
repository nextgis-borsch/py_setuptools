################################################################################
# Project:  Python packages
# Purpose:  CMake build scripts
# Author:   Dmitry Baryshnikov, dmitry.baryshnikov@nexgis.com
################################################################################
# Copyright (C) 2017-2018, NextGIS <info@nextgis.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################
cmake_minimum_required(VERSION 2.8.12 FATAL_ERROR)

project(setuptools)

if(NOT DEFINED PACKAGE_VENDOR)
    set(PACKAGE_VENDOR NextGIS)
endif()

if(NOT DEFINED PACKAGE_BUGREPORT)
    set(PACKAGE_BUGREPORT info@nextgis.com)
endif()


# some init settings
set(CMAKE_COLOR_MAKEFILE ON)
# set path to additional CMake modules
set(CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

if(OSX_FRAMEWORK AND (BUILD_SHARED_LIBS OR BUILD_STATIC_LIBS))
  message(FATAL_ERROR "Only OSX_FRAMEWORK key or any or both BUILD_SHARED_LIBS
                       and BUILD_STATIC_LIBS keys are permitted")
endif()

if(OSX_FRAMEWORK)
    message(FATAL_ERROR "Need fixes in setup.py for Darwin support")
    set(INSTALL_LIB_DIR "Library" CACHE INTERNAL "Installation directory for libraries" FORCE)
    set(CMAKE_MACOSX_RPATH ON)
else()
    set(INSTALL_LIB_DIR "." CACHE INTERNAL "Installation directory for libraries" FORCE)
endif()

if(NOT WITH_PYTHON2 AND NOT WITH_PYTHON3)
    set(WITH_PYTHON2 ON)
endif()

if(WITH_PYTHON2)
    find_package(PythonInterp 2)
    if(PYTHONINTERP_FOUND)
        set(PYTHON2_EXECUTABLE ${PYTHON_EXECUTABLE})
        set(PYTHON2_VERSION_MAJOR ${PYTHON_VERSION_MAJOR})
        set(PYTHON2_VERSION_MINOR ${PYTHON_VERSION_MINOR})
    else()
        message(WARNING "Cannot find python 2")
    endif()
endif()

unset(PYTHONINTERP_FOUND)
unset(PYTHON_EXECUTABLE)
unset(PYTHON_VERSION_MAJOR)
unset(PYTHON_VERSION_MINOR)

if(WITH_PYTHON3)
    # Hack, not find python3 withouut this
    find_program(PYTHON3_EXECUTABLE python3)
    set(PYTHON_EXECUTABLE ${PYTHON3_EXECUTABLE})

    find_package(PythonInterp 3)
    if(PYTHONINTERP_FOUND)
        set(PYTHON3_EXECUTABLE ${PYTHON_EXECUTABLE})
        set(PYTHON3_VERSION_MAJOR ${PYTHON_VERSION_MAJOR})
        set(PYTHON3_VERSION_MINOR ${PYTHON_VERSION_MINOR})
    else()
        message(WARNING "Cannot find python 3")
    endif()
endif()

if(NOT PYTHON2_EXECUTABLE AND NOT PYTHON3_EXECUTABLE)
    message(FATAL_ERROR "Cannot find python")
endif()

if(PYTHON2_EXECUTABLE)
    set(PYTHON_EXECUTABLE ${PYTHON2_EXECUTABLE})
else()
    set(PYTHON_EXECUTABLE ${PYTHON3_EXECUTABLE})
endif()


file(GLOB LOCAL_SOURCES_ARCHIVES LIST_DIRECTORIES false "*.zip")
if(LOCAL_SOURCES_ARCHIVES)
    list(GET LOCAL_SOURCES_ARCHIVES 0 LOCAL_SOURCES_ARCHIVE)
    string(REPLACE ".zip" "" LOCAL_SOURCES_VERSION ${LOCAL_SOURCES_ARCHIVE})
    string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}" "" LOCAL_SOURCES_VERSION ${LOCAL_SOURCES_VERSION})
    string(SUBSTRING ${LOCAL_SOURCES_VERSION} 12 -1 VERSION) # setuptools-
    message(STATUS "Local sources found: ${LOCAL_SOURCES_ARCHIVE}, version: ${VERSION}")
endif()

include(util)
get_compiler_version(COMPILER)

if(NOT LOCAL_SOURCES_ARCHIVE)
    file(DOWNLOAD "https://pypi.python.org/pypi/${PROJECT_NAME}/json" "${CMAKE_CURRENT_BINARY_DIR}/meta.json")

    # get version and download url
    execute_process(COMMAND ${PYTHON_EXECUTABLE}
        ${CMAKE_SOURCE_DIR}/cmake/pypi_process.py ${PLUGIN} ${CMAKE_CURRENT_BINARY_DIR}/meta.json ${COMPILER}
        OUTPUT_VARIABLE PACKAGE_DETAILS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    list(GET PACKAGE_DETAILS 0 DOWNLOAD_URL)
    list(GET PACKAGE_DETAILS 1 VERSION)
    list(GET PACKAGE_DETAILS 2 IN_VERSION)
    list(GET PACKAGE_DETAILS 3 PROJECT_CPACK_FILENAME)
endif()

report_version(${PROJECT_NAME} ${VERSION})

if(OSX_FRAMEWORK)
    set(FLAGS "ARCHFLAGS=-arch x86_64")
elseif(WIN32)
    if(MSVC_VERSION EQUAL 1400)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS80COMNTOOLS}")
    elseif(MSVC_VERSION EQUAL 1500)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS90COMNTOOLS}")
    elseif(MSVC_VERSION EQUAL 1600)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS100COMNTOOLS}")
    elseif(MSVC_VERSION EQUAL 1700)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS110COMNTOOLS}")
    elseif(MSVC_VERSION EQUAL 1800)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS120COMNTOOLS}")
    elseif(MSVC_VERSION EQUAL 1900)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=$ENV{VS140COMNTOOLS}")
    else() # 1912 - Need to copy vcvarsall.bat from VC\Auxiliary\Build to VC
        get_filename_component(_COMNTOOLS_PREFIX "${CMAKE_C_COMPILER}" PATH)
        get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        # get_filename_component(_COMNTOOLS_PREFIX "${_COMNTOOLS_PREFIX}" PATH)
        set(FLAGS ${FLAGS} "VS90COMNTOOLS=${_COMNTOOLS_PREFIX}")
    endif()
else()
    set(FLAGS "NextGIS=TRUE")
endif()

# Download tarbal
set(OUT_DIR_NAME ${PROJECT_NAME}-${IN_VERSION})
set(OUT_NAME "${OUT_DIR_NAME}.tar.gz")

if(LOCAL_SOURCES_ARCHIVE)
    file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/${OUT_NAME} DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
else()
    if(NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/${OUT_NAME}")
        status_message("Download ${DOWNLOAD_URL}")
        file(DOWNLOAD "${DOWNLOAD_URL}" "${CMAKE_CURRENT_BINARY_DIR}/${OUT_NAME}"
            SHOW_PROGRESS
        )
    endif()
endif()

# Extract archive
if(NOT EXISTS ${CMAKE_CURRENT_BINARY_DIR}/${OUT_DIR_NAME})
    status_message("Extract ${CMAKE_CURRENT_BINARY_DIR}/${OUT_NAME}")
    execute_process(COMMAND ${CMAKE_COMMAND} -E tar xzf ${CMAKE_CURRENT_BINARY_DIR}/${OUT_NAME})
endif()

macro(build_py ver)

    if(CMAKE_VERSION VERSION_LESS 3)
        set(PY_CMD ${PYTHON${ver}_EXECUTABLE})
    else()
        set(PY_CMD ${CMAKE_COMMAND} -E env "${FLAGS}" ${PYTHON${ver}_EXECUTABLE})
    endif()


    status_message("Configuring ...")
    execute_process(COMMAND ${PY_CMD} setup.py build ${BUILD_INCLUDES}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${OUT_DIR_NAME}
        OUTPUT_QUIET ERROR_QUIET
    )

    add_custom_target(build_py${ver} ALL
        COMMAND ${PY_CMD} setup.py build_ext ${BUILD_INCLUDES}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${OUT_DIR_NAME}
        VERBATIM
    )

    if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
        set(SETUP_OPTS ${SETUP_OPTS} --no-compile --single-version-externally-managed --record=rekord.txt --prefix=${CMAKE_CURRENT_BINARY_DIR}/inst_tmp)
    elseif(WIN32)
        string(REPLACE "/" "\\\\" TMP_PATH "${CMAKE_CURRENT_BINARY_DIR}/inst_tmp")
        set(SETUP_OPTS ${SETUP_OPTS} --no-compile --single-version-externally-managed --record=rekord.txt --prefix=${TMP_PATH})
    else()
        execute_process ( COMMAND ${PYTHON${ver}_EXECUTABLE} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" OUTPUT_VARIABLE PY_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)

        set(TEST_CMD "try:
    import setuptools
    print(1)
except ImportError:
    pass")

        execute_process ( COMMAND ${PYTHON${ver}_EXECUTABLE} -c ${TEST_CMD} OUTPUT_VARIABLE PY_HAVE_SETUPTOOLS OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(PY_HAVE_SETUPTOOLS)
            set(SETUP_OPTS ${SETUP_OPTS} --no-compile --single-version-externally-managed --record=rekord.txt)
        endif()

        string( LENGTH "$ENV{DESTDIR}" DESTDIRLEN )
        if ( ${DESTDIRLEN} GREATER 0 )
            set(SETUP_OPTS ${SETUP_OPTS} --root=$ENV{DESTDIR})
        elseif(PYTHON_DESTDIR)
            set(SETUP_OPTS ${SETUP_OPTS} --root=${PYTHON_DESTDIR})
        endif()

        # check debian
        string(FIND ${PY_SITE_PACKAGES} "dist-packages" PY_DIST_POS)
        if(${PY_DIST_POS} GREATER -1)
            set(SETUP_OPTS ${SETUP_OPTS} --install-layout=deb)
        endif()

        # TODO: do we need --install-lib=$(PYTHON_INSTALL_LIB) ?

        set(SETUP_OPTS ${SETUP_OPTS} --prefix=${CMAKE_CURRENT_BINARY_DIR}/inst_tmp)

    endif()
    add_custom_target(install_py${ver} ALL
        COMMAND ${PY_CMD} setup.py install ${SETUP_OPTS}
        DEPENDS build_py${ver}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${OUT_DIR_NAME}
        VERBATIM
    )
endmacro()

if(PYTHON2_EXECUTABLE)
    build_py(2)
endif()

if(PYTHON3_EXECUTABLE)
    build_py(3)
endif()

if(NOT SKIP_INSTALL_LIBRARIES AND NOT SKIP_INSTALL_ALL )
    install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/inst_tmp/ DESTINATION ${INSTALL_LIB_DIR})
endif()

# Archiving ====================================================================
set(PACKAGE_NAME ${PROJECT_NAME})

set(CPACK_PACKAGE_NAME "${PACKAGE_NAME}")
set(CPACK_PACKAGE_VENDOR "${PACKAGE_VENDOR}")
set(CPACK_PACKAGE_VERSION "${VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PACKAGE_NAME} Installation")
set(CPACK_PACKAGE_RELOCATABLE TRUE)
set(CPACK_ARCHIVE_COMPONENT_INSTALL ON)
set(CPACK_GENERATOR "ZIP")
set(CPACK_MONOLITHIC_INSTALL ON)
set(CPACK_STRIP_FILES TRUE)

# Get cpack zip archive name
set(CPACK_PACKAGE_FILE_NAME ${PROJECT_CPACK_FILENAME})

include(CPack)
