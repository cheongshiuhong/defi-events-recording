#!/bin/bash

set -e

mongo <<EOF
use admin

db.createUser({
  user: '$DB_USER',
  pwd:  '$DB_PASSWORD',
  roles: [{
    role: 'readWrite',
    db: '$DB_DATABASE'
  }]
})

db.getSiblingDB("database").createCollection('swaps');
db.getSiblingDB("database").getCollection("swaps").createIndex({ "event_id": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "block_hash": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "block_number": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "timestamp": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "transaction_hash": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "address": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "data.symbol_0": 1 });
db.getSiblingDB("database").getCollection("swaps").createIndex({ "data.symbol_1": 1 });
EOF
