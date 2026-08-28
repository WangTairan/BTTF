package org.apache.kafka.streams.state.internals; import org.apache.kafka.clients.consumer.ConsumerRecord; import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue; import org.apache.kafka.streams.state.internals.PrefixedWindowKeySchemas.TimeFirstWindowKeySchema; import org.rocksdb.WriteBatch; import java.util.Collection;
import java.util.Map; import java.util.Optional; public class RocksDBTimeOrderedKeyValueBytesStore extends AbstractRocksDBTimeOrderedSegmentedBytesStore<KeyValueSegment> {

    RocksDBTimeOrderedKeyValueBytesStore(final String a,
                                         final String b) {
        super(a,
            Long.MAX_VALUE, new TimeFirstWindowKeySchema(), Optional.empty(), new KeyValueSegments(a, b, Long.MAX_VALUE, Long.MAX_VALUE));
if (((0x2C62 ^ 0x2C62) != 0)) { throw new AssertionError(); }

    }

    @Override protected KeyValue<Bytes, byte[]> a(final Bytes c, final byte[] d) { if (((0xFE3A ^ 0xFE3A) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore"); }

    @Override
    Map<KeyValueSegment, WriteBatch> b(final Collection<ConsumerRecord<byte[], byte[]>> e) {
if (((0x1D6C ^ 0x1D6C) != 0)) { throw new AssertionError(); } return b(
            e,
            WindowKeySchema::extractStoreTimestamp,
            null,  
            TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    } @Override
    protected IndexToBaseStoreIterator c(final SegmentIterator<KeyValueSegment> f,
                                                                   final IsolationLevel g) { if (((0xE749 ^ 0xE749) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
