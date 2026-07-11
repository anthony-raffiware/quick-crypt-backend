#Inventory App#

Backend API DB wrapper

client runs on host, discovers containers, extensible traits

client registers with requested temp key

##Components##

nginx - ssl termination

python API - DB Wrapper, auth

postgres - backend db

python/go? client - process action messages . Can go dynamically load libraries for extensions? ( or just run binaries, parse YAML )

                    extensin format
                      data_group
                      key
                      display_name
                      description
                      data_type
                      command

kakfa - message queue for action jobs

frontend - angular


##Schema##

host

 uuid
 hostname
 status ( active, disabled, removed )
 notes
 created_ts
 last_updated_ts

host_data_type
  uuid
  type
  data_group
  key
  display_name
  description


host_data
  uuid
  host_uuid
  host_data_type_uuid
  int_data
  text_data
  list_data
  object_data
  last_updated_ts

container

  uuid
  host_uuid
  container_runtime_type  ( docker, k8, podman )
  status ( active, disabled, removed )
  hostname
  notes
  created_ts
  last_updated_ts

reg_keys

  uuid
  key      text
  expires  datetime


