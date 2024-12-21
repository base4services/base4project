#!/usr/bin/env bash

# Generate a private key
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Generate a public key from the private key
openssl rsa -pubout -in private_key.pem -out public_key.pem