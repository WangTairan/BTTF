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
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator;

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator) {
        this.innerIterator = innerIterator;
    }

    @Override
    public void close() {
        innerIterator.close();
    }

    @Override
    public Windowed<Bytes> peekNextKey() {
        return innerIterator.peekNextKey();
    }

    @Override
    public boolean hasNext() {
        return innerIterator.hasNext();
    }

    @Override
    public KeyValue<Windowed<Bytes>, byte[]> next() {
        final KeyValue<Windowed<Bytes>, byte[]> keyValue = innerIterator.next();
        if (keyValue == null) {
            return null;
        }
        return KeyValue.pair(keyValue.key, convertToHeaderFormat(keyValue.value));
    }
}
