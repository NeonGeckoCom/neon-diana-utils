# Deploying Nominatim
The [unofficial Helm Charts](https://nominatim.org/release-docs/latest/admin/Installation/) come with 
(documentation here)[https://github.com/robjuz/helm-charts/blob/master/charts/nominatim/README.md].
The instructions here are based upon that documentation.
> The cluster will need at least 4GB of available memory (on the node where this
> is deployed) to perform initialization. If this isn't possible, update 
> `init_values.yaml` to use less `maintenance_work_mem` and consider updating 
> `pbfUrl` to use a smaller region instead of the global data.

## Initializing the Nominatim Services
Some default values files are included with Diana.
To initialize Nominatim with global data to its own namespace:
```shell
helm upgrade -n nominatim nominatim robjuz/nominatim -f neon_diana_utils/nominatim/init_values.yaml
```

This will likely take on the order of hours to complete. You may use the Dashboard
or k9s to monitor the job `nominatim-init` (in the `nominatim` namespace). If the
job is interrupted, it is possible that the database is left in a corrupted state;
it is recommended to `kubectl delete namespace nominatim` and start over if the
init process is interrupted.
> Note: The Kubernetes Dashboard may show the `nominatim-init` job as having 1
> completion before the job has completed. `k9s` does not appear to have this bug.
> If you can't use `k9s` then consider watching the Job logs to make sure the init
> actually completes.