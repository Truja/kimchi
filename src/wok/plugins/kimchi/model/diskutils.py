#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

from wok.exception import OperationFailed, NotFoundError
from wok.utils import wok_log

from wok.plugins.kimchi.model.vms import VMModel, VMsModel
from wok.plugins.kimchi.xmlutils.disk import get_vm_disk_info, get_vm_disks


"""
    Functions that multiple storage-related models (e.g. VMStoragesModel,
    VolumesModel) will need.
"""


def get_disk_used_by(objstore, conn, path):
    try:
        with objstore as session:
            try:
                used_by = session.get('storagevolume', path)['used_by']
            except (KeyError, NotFoundError):
                wok_log.info('Volume %s not found in obj store.' % path)
                used_by = []
                # try to find this volume in existing vm
                vms_list = VMsModel.get_vms(conn)
                for vm in vms_list:
                    dom = VMModel.get_vm(vm, conn)
                    storages = get_vm_disks(dom)
                    for disk in storages.keys():
                        d_info = get_vm_disk_info(dom, disk)
                        if path == d_info['path']:
                            used_by.append(vm)
                try:
                    session.store('storagevolume', path,
                                  {'used_by': used_by})
                except Exception as e:
                    # Let the exception be raised. If we allow disks'
                    #   used_by to be out of sync, data corruption could
                    #   occour if a disk is added to two guests
                    #   unknowingly.
                    wok_log.error('Unable to store storage volume id in'
                                  ' objectstore due error: %s',
                                  e.message)
                    raise OperationFailed('KCHVOL0017E',
                                          {'err': e.message})
    except Exception as e:
        # This exception is going to catch errors returned by 'with',
        # specially ones generated by 'session.store'. It is outside
        # to avoid conflict with the __exit__ function of 'with'
        raise OperationFailed('KCHVOL0017E', {'err': e.message})
    return used_by


def set_disk_used_by(objstore, path, new_used_by):
    try:
        with objstore as session:
            session.store('storagevolume', path, {'used_by': new_used_by})
    except Exception as e:
        raise OperationFailed('KCHVOL0017E', {'err': e.message})