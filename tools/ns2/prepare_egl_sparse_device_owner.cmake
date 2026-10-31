# SPDX-License-Identifier: GPL-3.0-or-later
# N58 adds a strict query; sparse image allocation remains unimplemented.
if(NOT DEFINED INPUT OR NOT DEFINED OUTPUT)
    message(FATAL_ERROR "N58 INPUT and OUTPUT required")
endif()
if(NOT EXISTS "${INPUT}")
    message(FATAL_ERROR "N58 Vulkan device source owner missing")
endif()
file(READ "${INPUT}" body)
set(anchor [==[    bool IsSparseBindingSupported() const {
        return features.features.sparseBinding && graphics_family_sparse_binding;
    }]==])
set(replacement [==[    bool IsSparseBindingSupported() const {
        return features.features.sparseBinding && graphics_family_sparse_binding;
    }

    // N58: image sparse residency requires a stronger Vulkan feature than
    // sparse resource binding. Never treat the two as interchangeable.
    [[nodiscard]] bool IsSparseResidencyImage2DSupported() const {
        return IsSparseBindingSupported() && features.features.sparseResidencyImage2D;
    }]==])
string(FIND "${body}" "${anchor}" first)
if(first LESS 0)
    message(FATAL_ERROR "N58 Vulkan sparse-binding owner drift")
endif()
string(LENGTH "${anchor}" length)
math(EXPR next "${first} + ${length}")
string(SUBSTRING "${body}" ${next} -1 tail)
string(FIND "${tail}" "${anchor}" other)
if(NOT other LESS 0)
    message(FATAL_ERROR "N58 ambiguous Vulkan source owner")
endif()
string(REPLACE "${anchor}" "${replacement}" body "${body}")
get_filename_component(parent "${OUTPUT}" DIRECTORY)
file(MAKE_DIRECTORY "${parent}")
file(WRITE "${OUTPUT}" "${body}")
