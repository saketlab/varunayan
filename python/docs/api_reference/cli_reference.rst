CLI Reference
=============

The ``varunayan`` command has three subcommands. Each one calls the Python
function with the same name.

.. list-table::
   :header-rows: 1

   * - Subcommand
     - Python function
     - Region options
   * - ``varunayan geojson``
     - :func:`varunayan.era5ify_geojson`
     - ``--geojson FILE``, ``--level {union,feature}``
   * - ``varunayan bbox``
     - :func:`varunayan.era5ify_bbox`
     - ``--north``, ``--south``, ``--east``, ``--west``
   * - ``varunayan point``
     - :func:`varunayan.era5ify_point`
     - ``--lat``, ``--lon``

All subcommands take ``--request-id``, ``--variables``, ``--start``, ``--end``,
``--dataset-type``, ``--pressure-levels``, ``--freq``, ``--res``,
``--verbosity`` and ``--save-raw``.

.. code-block:: bash

    varunayan geojson \
        --request-id "india_weather" \
        --variables "2m_temperature,total_precipitation" \
        --start "2023-01-01" --end "2023-01-31" \
        --geojson "india.geojson" --freq "daily"

See :doc:`../cli_reference` for all options and the output files.
