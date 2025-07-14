LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := resize_userdata.sh
LOCAL_MODULE_CLASS := EXECUTABLES
LOCAL_SRC_FILES := resize_userdata.sh
LOCAL_MODULE_PATH := $(TARGET_OUT)/bin
LOCAL_MODULE_TAGS := optional
include $(BUILD_PREBUILT)
