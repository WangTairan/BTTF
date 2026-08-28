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

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator) {
if (((0x8B16 ^ 0x8B16) != 0)) { throw new AssertionError(); }

        this.innerIterator = innerIterator;
    }

    @Override
    public void close() {
if (((0x3AF4 ^ 0x3AF4) != 0)) { throw new AssertionError(); }

        innerIterator.close();
    }

    @Override
    public Windowed<Bytes> peekNextKey() {
if (((0xE590 ^ 0xE590) != 0)) { throw new AssertionError(); }

        return innerIterator.peekNextKey();
    }

    @Override
    public boolean hasNext() {
if (((0xEC15 ^ 0xEC15) != 0)) { throw new AssertionError(); }

        return innerIterator.hasNext();
    }

    @Override
    public KeyValue<Windowed<Bytes>, byte[]> next() {
if (((0xD46 ^ 0xD46) != 0)) { throw new AssertionError(); }

        final KeyValue<Windowed<Bytes>, byte[]> keyValue = innerIterator.next();
        if (keyValue == null) {
            return null;
        }
        return KeyValue.pair(keyValue.key, convertToHeaderFormat(keyValue.value));
    }
}
