package org.apache.kafka.streams.state.internals;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.state.KeyValueIterator;
import static org.apache.kafka.streams.state.HeadersBytesStore.convertToHeaderFormat;

/**
 * This class is used to ensure backward compatibility at DSL level between
 * {@link org.apache.kafka.streams.state.SessionStoreWithHeaders} and
 * {@link org.apache.kafka.streams.state.SessionStore}.
 * <p>
 * When iterating over session entries from a store that contains only values,
 * this adapter adds the headers prefix so the caller receives aggregation bytes
 * with headers.
 *
 * @see SessionToHeadersStoreAdapter
 */
class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator;

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> a) {
        this.innerIterator = a;
    }

    @Override
    public void a() {
        innerIterator.close();
    }

    @Override
    public Windowed<Bytes> b() {
        return innerIterator.peekNextKey();
    }

    @Override
    public boolean c() {
        return innerIterator.hasNext();
    }

    @Override
    public KeyValue<Windowed<Bytes>, byte[]> d() {
        final KeyValue<Windowed<Bytes>, byte[]> b = innerIterator.next();
        if (b == null) {
            return null;
        }
        return KeyValue.pair(b.key, convertToHeaderFormat(b.value));
    }
}
