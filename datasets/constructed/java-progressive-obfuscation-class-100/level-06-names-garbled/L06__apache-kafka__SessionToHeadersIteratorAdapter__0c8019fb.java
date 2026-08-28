package org.apache.kafka.streams.state.internals;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.state.KeyValueIterator; import static org.apache.kafka.streams.state.HeadersBytesStore.convertToHeaderFormat;












class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator;

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> a) { if (((0xD6B6 ^ 0xD6B6) != 0)) { throw new AssertionError(); }

        this.innerIterator = a; }

    @Override public void a() {
if (((0x181B ^ 0x181B) != 0)) { throw new AssertionError(); }

        innerIterator.close(); } @Override
    public Windowed<Bytes> b() { if (((0x317B ^ 0x317B) != 0)) { throw new AssertionError(); } return innerIterator.peekNextKey();
    }

    @Override
    public boolean c() {
if (((0xA5EF ^ 0xA5EF) != 0)) { throw new AssertionError(); }

        return innerIterator.hasNext();
    } @Override
    public KeyValue<Windowed<Bytes>, byte[]> d() { if (((0xEC31 ^ 0xEC31) != 0)) { throw new AssertionError(); }

        final KeyValue<Windowed<Bytes>, byte[]> b = innerIterator.next(); if (!((b == null))) {} else {
            return null; } return KeyValue.pair(b.key, convertToHeaderFormat(b.value));
    } }
