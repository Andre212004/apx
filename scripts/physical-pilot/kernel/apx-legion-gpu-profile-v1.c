// SPDX-License-Identifier: GPL-2.0-only
/* Target-bound Lenovo Legion GPU profile bridge for the APX physical pilot. */

#include <linux/acpi.h>
#include <linux/dmi.h>
#include <linux/kobject.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/sysfs.h>
#include <linux/wmi.h>

#define APX_GAMEZONE_GUID "887B54E3-DDDC-4B2C-8B88-68A26A8835D0"
#define APX_WMI_IS_SUPPORT_HYBRID 40
#define APX_WMI_GET_HYBRID 41
#define APX_WMI_SET_HYBRID 42
#define APX_WMI_IS_SUPPORT_IGPU 63
#define APX_WMI_GET_IGPU 64
#define APX_WMI_SET_IGPU 65

static struct kobject *apx_kobject;
static DEFINE_MUTEX(apx_wmi_lock);
static unsigned long hybrid_supported;
static unsigned long igpu_supported;

static int apx_wmi_read(u32 method, unsigned long *value)
{
	struct acpi_buffer input = { 0, NULL };
	struct acpi_buffer output = { ACPI_ALLOCATE_BUFFER, NULL };
	union acpi_object *object;
	acpi_status status;

	status = wmi_evaluate_method(APX_GAMEZONE_GUID, 0, method, &input,
				     &output);
	if (ACPI_FAILURE(status))
		return -EIO;
	object = output.pointer;
	if (!object || object->type != ACPI_TYPE_INTEGER) {
		kfree(object);
		return -EPROTO;
	}
	*value = object->integer.value;
	kfree(object);
	return 0;
}

static int apx_wmi_write(u32 method, u8 value)
{
	struct acpi_buffer input = { sizeof(value), &value };
	acpi_status status;

	status = wmi_evaluate_method(APX_GAMEZONE_GUID, 0, method, &input, NULL);
	return ACPI_FAILURE(status) ? -EIO : 0;
}

static ssize_t hybrid_supported_show(struct kobject *kobj,
				     struct kobj_attribute *attr, char *buffer)
{
	return sysfs_emit(buffer, "%lu\n", hybrid_supported);
}

static ssize_t igpu_supported_show(struct kobject *kobj,
				   struct kobj_attribute *attr, char *buffer)
{
	return sysfs_emit(buffer, "%lu\n", igpu_supported);
}

static ssize_t hybrid_mode_show(struct kobject *kobj,
				struct kobj_attribute *attr, char *buffer)
{
	unsigned long raw;
	int error;

	mutex_lock(&apx_wmi_lock);
	error = apx_wmi_read(APX_WMI_GET_HYBRID, &raw);
	mutex_unlock(&apx_wmi_lock);
	if (error)
		return error;
	/* Lenovo reports zero for enabled Hybrid Mode. */
	return sysfs_emit(buffer, "%u\n", !raw);
}

static ssize_t hybrid_mode_store(struct kobject *kobj,
				 struct kobj_attribute *attr, const char *buffer,
				 size_t count)
{
	bool enabled;
	int error;

	error = kstrtobool(buffer, &enabled);
	if (error)
		return error;
	mutex_lock(&apx_wmi_lock);
	error = apx_wmi_write(APX_WMI_SET_HYBRID, !enabled);
	mutex_unlock(&apx_wmi_lock);
	return error ? error : count;
}

static ssize_t igpu_mode_show(struct kobject *kobj,
			      struct kobj_attribute *attr, char *buffer)
{
	unsigned long value;
	int error;

	mutex_lock(&apx_wmi_lock);
	error = apx_wmi_read(APX_WMI_GET_IGPU, &value);
	mutex_unlock(&apx_wmi_lock);
	if (error)
		return error;
	return sysfs_emit(buffer, "%lu\n", value);
}

static ssize_t igpu_mode_store(struct kobject *kobj,
			       struct kobj_attribute *attr, const char *buffer,
			       size_t count)
{
	u8 value;
	int error;

	error = kstrtou8(buffer, 0, &value);
	if (error)
		return error;
	if (value > 2)
		return -EINVAL;
	mutex_lock(&apx_wmi_lock);
	error = apx_wmi_write(APX_WMI_SET_IGPU, value);
	mutex_unlock(&apx_wmi_lock);
	return error ? error : count;
}

static struct kobj_attribute hybrid_supported_attribute =
	__ATTR_RO(hybrid_supported);
static struct kobj_attribute igpu_supported_attribute =
	__ATTR_RO(igpu_supported);
static struct kobj_attribute hybrid_mode_attribute =
	__ATTR(hybrid_mode, 0600, hybrid_mode_show, hybrid_mode_store);
static struct kobj_attribute igpu_mode_attribute =
	__ATTR(igpu_mode, 0600, igpu_mode_show, igpu_mode_store);

static struct attribute *apx_attributes[] = {
	&hybrid_supported_attribute.attr,
	&igpu_supported_attribute.attr,
	&hybrid_mode_attribute.attr,
	&igpu_mode_attribute.attr,
	NULL,
};

static const struct attribute_group apx_attribute_group = {
	.attrs = apx_attributes,
};

static int __init apx_legion_gpu_profile_init(void)
{
	int error;

	if (!dmi_match(DMI_SYS_VENDOR, "LENOVO") ||
	    !dmi_match(DMI_PRODUCT_NAME, "82JU"))
		return -ENODEV;
	if (!wmi_has_guid(APX_GAMEZONE_GUID))
		return -ENODEV;
	error = apx_wmi_read(APX_WMI_IS_SUPPORT_HYBRID, &hybrid_supported);
	if (error)
		return error;
	error = apx_wmi_read(APX_WMI_IS_SUPPORT_IGPU, &igpu_supported);
	if (error)
		return error;
	if (!hybrid_supported)
		return -EOPNOTSUPP;

	apx_kobject = kobject_create_and_add("apx_legion_gpu_profile_v1",
					      kernel_kobj);
	if (!apx_kobject)
		return -ENOMEM;
	error = sysfs_create_group(apx_kobject, &apx_attribute_group);
	if (error) {
		kobject_put(apx_kobject);
		apx_kobject = NULL;
		return error;
	}
	pr_info("APX Legion GPU profile bridge loaded (hybrid=%lu, igpu=%lu)\n",
		hybrid_supported, igpu_supported);
	return 0;
}

static void __exit apx_legion_gpu_profile_exit(void)
{
	if (apx_kobject) {
		sysfs_remove_group(apx_kobject, &apx_attribute_group);
		kobject_put(apx_kobject);
	}
}

module_init(apx_legion_gpu_profile_init);
module_exit(apx_legion_gpu_profile_exit);

MODULE_AUTHOR("APX physical pilot");
MODULE_DESCRIPTION("Target-bound Lenovo Legion 5 15ACH6H GPU profile bridge");
MODULE_LICENSE("GPL");
