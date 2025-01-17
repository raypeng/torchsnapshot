#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import unittest

from torchsnapshot.manifest import (
    ChunkedTensorEntry,
    DictEntry,
    get_available_entries,
    ObjectEntry,
    Shard,
    ShardedTensorEntry,
    SnapshotMetadata,
    TensorEntry,
)

_MANIFEST = {
    "0/foo": DictEntry(
        keys=["bar", "baz", "qux", "quuux", "qux_chunked", "quux_chunked"]
    ),
    "0/foo/bar": ObjectEntry(
        location="0/foo/bar", serializer="torch_save", obj_type="Bar", replicated=False
    ),
    "0/foo/baz": ObjectEntry(
        location="replicated/foo/baz",
        serializer="torch_save",
        obj_type="Baz",
        replicated=True,
    ),
    "0/foo/qux": ShardedTensorEntry(
        shards=[
            Shard(
                offsets=[0, 0],
                sizes=[4, 4],
                tensor=TensorEntry(
                    location="sharded/foo/qux.0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[2, 8],
                    replicated=False,
                ),
            )
        ]
    ),
    "0/foo/quux": TensorEntry(
        location="0/foo/quux",
        serializer="torch_save",
        dtype="float32",
        shape=[128, 128],
        replicated=False,
    ),
    "0/foo/qux_chunked": ChunkedTensorEntry(
        dtype="float32",
        shape=[7, 10],
        chunks=[
            Shard(
                offsets=[0, 0],
                sizes=[5, 10],
                tensor=TensorEntry(
                    location="replicated/foo/qux_chunked_0_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[5, 10],
                    replicated=False,
                ),
            ),
            Shard(
                offsets=[5, 0],
                sizes=[2, 10],
                tensor=TensorEntry(
                    location="replicated/foo/qux_chunked_5_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[2, 10],
                    replicated=False,
                ),
            ),
        ],
        replicated=True,
    ),
    "0/foo/quux_chunked": ChunkedTensorEntry(
        dtype="float32",
        shape=[100],
        chunks=[
            Shard(
                offsets=[0],
                sizes=[50],
                tensor=TensorEntry(
                    location="0/foo/qux_chunked_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[50],
                    replicated=False,
                ),
            ),
            Shard(
                offsets=[50],
                sizes=[50],
                tensor=TensorEntry(
                    location="0/foo/qux_chunked_50",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[50],
                    replicated=False,
                ),
            ),
        ],
        replicated=False,
    ),
    "1/foo": DictEntry(
        keys=["bar", "baz", "qux", "quuux", "qux_chunked", "quux_chunked"]
    ),
    "1/foo/bar": ObjectEntry(
        location="1/foo/bar", serializer="torch_save", obj_type="Bar", replicated=False
    ),
    "1/foo/baz": ObjectEntry(
        location="replicated/foo/baz",
        serializer="torch_save",
        obj_type="Baz",
        replicated=True,
    ),
    "1/foo/qux": ShardedTensorEntry(
        shards=[
            Shard(
                offsets=[4, 0],
                sizes=[4, 4],
                tensor=TensorEntry(
                    location="sharded/foo/qux.1",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[2, 8],
                    replicated=False,
                ),
            )
        ]
    ),
    "1/foo/quux": TensorEntry(
        location="1/foo/quux",
        serializer="torch_save",
        dtype="float32",
        shape=[128, 128],
        replicated=False,
    ),
    "1/foo/qux_chunked": ChunkedTensorEntry(
        dtype="float32",
        shape=[7, 10],
        chunks=[
            Shard(
                offsets=[0, 0],
                sizes=[5, 10],
                tensor=TensorEntry(
                    location="replicated/foo/qux_chunked_0_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[5, 10],
                    replicated=False,
                ),
            ),
            Shard(
                offsets=[5, 0],
                sizes=[2, 10],
                tensor=TensorEntry(
                    location="replicated/foo/qux_chunked_5_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[2, 10],
                    replicated=False,
                ),
            ),
        ],
        replicated=True,
    ),
    "1/foo/quux_chunked": ChunkedTensorEntry(
        dtype="float32",
        shape=[100],
        chunks=[
            Shard(
                offsets=[0],
                sizes=[50],
                tensor=TensorEntry(
                    location="1/foo/qux_chunked_0",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[50],
                    replicated=False,
                ),
            ),
            Shard(
                offsets=[50],
                sizes=[50],
                tensor=TensorEntry(
                    location="1/foo/qux_chunked_50",
                    serializer="torch_save",
                    dtype="float32",
                    shape=[50],
                    replicated=False,
                ),
            ),
        ],
        replicated=False,
    ),
}


class ManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_yaml(self) -> None:
        metadata = SnapshotMetadata(
            version="0.0.0",
            world_size=2,
            manifest=_MANIFEST,
        )
        yaml_str = metadata.to_yaml()
        loaded_metadata = SnapshotMetadata.from_yaml(yaml_str=yaml_str)
        self.assertDictEqual(metadata.manifest, loaded_metadata.manifest)

    def test_load_with_same_world_size_rank_zero(self) -> None:
        available_entries = get_available_entries(_MANIFEST, 0)
        expected_available_entries = {
            "foo/bar": ObjectEntry(
                location="0/foo/bar",
                serializer="torch_save",
                obj_type="Bar",
                replicated=False,
            ),
            "foo/baz": ObjectEntry(
                location="replicated/foo/baz",
                serializer="torch_save",
                obj_type="Baz",
                replicated=True,
            ),
            "foo/qux": ShardedTensorEntry(
                shards=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[4, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.1",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                ]
            ),
            "foo/quux": TensorEntry(
                location="0/foo/quux",
                serializer="torch_save",
                dtype="float32",
                shape=[128, 128],
                replicated=False,
            ),
            "foo/qux_chunked": ChunkedTensorEntry(
                dtype="float32",
                shape=[7, 10],
                chunks=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[5, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_0_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[5, 10],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[5, 0],
                        sizes=[2, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_5_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 10],
                            replicated=False,
                        ),
                    ),
                ],
                replicated=True,
            ),
            "foo/quux_chunked": ChunkedTensorEntry(
                dtype="float32",
                shape=[100],
                chunks=[
                    Shard(
                        offsets=[0],
                        sizes=[50],
                        tensor=TensorEntry(
                            location="0/foo/qux_chunked_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[50],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[50],
                        sizes=[50],
                        tensor=TensorEntry(
                            location="0/foo/qux_chunked_50",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[50],
                            replicated=False,
                        ),
                    ),
                ],
                replicated=False,
            ),
        }
        self.assertDictEqual(available_entries, expected_available_entries)

    def test_load_with_same_world_size_rank_one(self) -> None:
        available_entries = get_available_entries(_MANIFEST, 1)
        expected_available_entries = {
            "foo/bar": ObjectEntry(
                location="1/foo/bar",
                serializer="torch_save",
                obj_type="Bar",
                replicated=False,
            ),
            "foo/baz": ObjectEntry(
                location="replicated/foo/baz",
                serializer="torch_save",
                obj_type="Baz",
                replicated=True,
            ),
            "foo/qux": ShardedTensorEntry(
                shards=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[4, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.1",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                ]
            ),
            "foo/quux": TensorEntry(
                location="1/foo/quux",
                serializer="torch_save",
                dtype="float32",
                shape=[128, 128],
                replicated=False,
            ),
            "foo/qux_chunked": ChunkedTensorEntry(
                dtype="float32",
                shape=[7, 10],
                chunks=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[5, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_0_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[5, 10],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[5, 0],
                        sizes=[2, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_5_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 10],
                            replicated=False,
                        ),
                    ),
                ],
                replicated=True,
            ),
            "foo/quux_chunked": ChunkedTensorEntry(
                dtype="float32",
                shape=[100],
                chunks=[
                    Shard(
                        offsets=[0],
                        sizes=[50],
                        tensor=TensorEntry(
                            location="1/foo/qux_chunked_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[50],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[50],
                        sizes=[50],
                        tensor=TensorEntry(
                            location="1/foo/qux_chunked_50",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[50],
                            replicated=False,
                        ),
                    ),
                ],
                replicated=False,
            ),
        }
        self.assertDictEqual(available_entries, expected_available_entries)

    def test_load_with_larger_world_size(self) -> None:
        available_entries = get_available_entries(_MANIFEST, 42)
        expected_available_entries = {
            "foo/baz": ObjectEntry(
                location="replicated/foo/baz",
                serializer="torch_save",
                obj_type="Baz",
                replicated=True,
            ),
            "foo/qux": ShardedTensorEntry(
                shards=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[4, 0],
                        sizes=[4, 4],
                        tensor=TensorEntry(
                            location="sharded/foo/qux.1",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 8],
                            replicated=False,
                        ),
                    ),
                ]
            ),
            "foo/qux_chunked": ChunkedTensorEntry(
                dtype="float32",
                shape=[7, 10],
                chunks=[
                    Shard(
                        offsets=[0, 0],
                        sizes=[5, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_0_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[5, 10],
                            replicated=False,
                        ),
                    ),
                    Shard(
                        offsets=[5, 0],
                        sizes=[2, 10],
                        tensor=TensorEntry(
                            location="replicated/foo/qux_chunked_5_0",
                            serializer="torch_save",
                            dtype="float32",
                            shape=[2, 10],
                            replicated=False,
                        ),
                    ),
                ],
                replicated=True,
            ),
        }
        self.assertDictEqual(available_entries, expected_available_entries)
