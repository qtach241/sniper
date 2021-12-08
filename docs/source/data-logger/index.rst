Firmware Updates
################

Message Format
==============

Firmware Updates to the GW and EM utilize the ``FirmwareUpdate`` protobuf message to carry data over MQTT from client sender to destination.

.. code-block::

    message FirmwareUpdate {
        string gw_firmware_ver = 1;
        bytes gw_firmware_hash = 2;
        bytes gw_firmware = 3;
        string em_firmware_ver = 4;
        bytes em_firmware_hash = 5;
        bytes em_firmware = 6;
    }

The protobuf encodes data for both Gateway and EM firmware (version, hash, and image).

.. note::

	``gw_firmware_ver`` should be the Image ID of the exported Docker repository. This can either be the full SHA256 ID or the shortened version usually reported by the ``Docker Images`` command.

	``gw_firmware`` contains the actual GW Docker Image data exported via the ``Docker Save`` command and optionally compressed using bzip2 or gzip compression.

The Gateway behaves differently depending on which fields of the protobuf message are populated vs empty, and which topic the message was received on.

Initiating an Update
====================

A firmware update is initiated when clients publish a ``FirmwareUpdate`` protobuf message to one of the **Firmware** topic(s) below.

``firmware``
	- Messages published to this topic will be received by ALL Gateways currently connected to the master broker.
	- If ``gw_firmware``, ``gw_firmware_hash``, and ``gw_firmware_ver`` are provided, all Gateways will be updated.
	- If ``em_firmware``, ``em_firmware_hash``, and ``em_firmware_ver`` are provided, all attached EMs to all Gateways will be updated.
``<IoX-UUID>/firmware``
	- Messages published to this topic will be received by a single Gateway.
	- If ``gw_firmware``, ``gw_firmware_hash``, and ``gw_firmware_ver`` are provided, the target Gateway will be updated.
	- If ``em_firmware``, ``em_firmware_hash``, and ``em_firmware_ver`` are provided, all attached EMs to the target Gateway will be updated. 
``<IoX-UUID>/<ExMo-UUID>/firmware``
	- Messages published to this topic will be received by a single Gateway and forwared to a single attached EM.
	- The ``gw_firmware``, ``gw_firmware_hash``, and ``gw_firmware_ver`` must be empty. If provided, the Gateway will report an error.
	- If ``em_firmware``, ``em_firmware_hash``, and ``em_firmware_ver`` are provided, the target EM will be updated.

Initiating a Rollback
=====================

A firmware rollback is initiated when the ``gw_firmware_ver`` or ``em_firmware_ver`` field is provided, but the corresponding ``gw_firmware`` and ``em_firmware`` fields are empty.

In the case of the Gateway, the ``gw_firmware_ver`` selects an existing Image in the local Docker registry (via Image ID) to be loaded.

EMs currently only save a single firmware image for rollback purposes. If ``em_firmware_ver`` is provided but ``em_firmware`` is empty, the EM will trigger a firmware rollback to the previous version stored in the "rollback" slot.

Reporting Results
=================

Clients should subscribe to the following topics to monitor firmware version of the Gateways/EMs. Gateways/EMs automatically publish firmware version info after connecting with the broker. This can be used to verify that the entire firmware update process was completed successfully.

- ``<IoX-UUID>/firmware_version``
- ``<IoX-UUID>/<ExMo-UUID>/firmware_version``

The Gateway will also report firmware status (including error messages) to the ``firmware_status`` topic(s).

- ``<IoX-UUID>/firmware_status``
- ``<IoX-UUID>/<ExMo-UUID>/firmware_status``


Python Script Examples
======================

The following python scripts are provided to exercise and test the firmware update API in lieue of another client application. These scripts may be run inside the provided system tests docker container.

- firmware_update_gw.py
- firmware_update_em.py

The --help parameter lists the expected usage details / options for each script:

.. code-block::

	$ docker run --rm -v $(pwd)/logs:/logs --net=host demo_system_tests python firmware_update_gw.py --help
	Usage: firmware_update_gw.py -h <MQTT Broker> -U <IoX GUID> [-u <ExMo GUID> -F <gw_filename> -f <em_filename> -V <gw_ver> -v <em_ver>]


The following example shows how to update the Gateway with a new Docker image. The **-F** parameter must be a docker image archive.

.. code-block::

	$ docker run --rm -v $(pwd)/logs:/logs --net=host demo_system_tests python firmware_update_gw.py -h "18.220.240.96" -U test_gw -V anything -F image.tar.bz2

.. note::

	Note that for loading a new Docker image, the version string (Image ID) is automatically extracted from the image archive passed in the **-F** parameter during the loading process. The version field passed as the **-V** parameter, however, must not be empty.

The following example shows how to perform a "rollback" of the Gateway Docker image to a previous version. The **-V** parameter must be the Docker Image ID to rollback to.

.. code-block::

	$ docker run --rm -v $(pwd)/logs:/logs --net=host demo_system_tests python firmware_update_gw.py -h "18.220.240.96" -U test_gw -V f08a5d9edbeb

.. note::

	To obtain a list of all Docker images and their IDs currently on the Gateway, request a **Product Version Report** from the Gateway and inspect the ``firmware_ver`` field in the response. This field contains the JSON string output equivalent of running ``Docker Images`` from the linux terminal. The **current** image will be the one tagged as ``compasssolutions/psgg:latest`` while older images will be untagged.

The following example shows how to perform a firmware update for a single EM:

.. code-block::

	$ docker run --rm -v $(pwd)/logs:/logs --net=host demo_system_tests python firmware_update_em.py -h "18.220.240.96" -U test_gw -u test_em -f psgg-exmo.bin

The following example shows how to perform a firmware "rollback" for a single EM attached to a specific Gateway.

.. code-block::

	$ TBD

The following example shows how to perform a firmware update for all EMs attached to a specific Gateway.

.. code-block::

	$ TBD