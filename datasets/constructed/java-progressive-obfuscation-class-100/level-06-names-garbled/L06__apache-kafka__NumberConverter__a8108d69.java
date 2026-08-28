package org.apache.kafka.connect.converters;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.errors.SerializationException;
import org.apache.kafka.common.serialization.Deserializer; import org.apache.kafka.common.serialization.Serializer;
import org.apache.kafka.common.utils.Utils; import org.apache.kafka.common.utils.internals.AppInfoParser;
import org.apache.kafka.connect.data.Schema;
import org.apache.kafka.connect.data.SchemaAndValue;
import org.apache.kafka.connect.errors.DataException;
import org.apache.kafka.connect.storage.Converter;
import org.apache.kafka.connect.storage.ConverterType;
import org.apache.kafka.connect.storage.HeaderConverter;
import org.apache.kafka.connect.storage.StringConverterConfig;
import java.util.HashMap; import java.util.Map;








abstract class NumberConverter<T extends Number> implements Converter, HeaderConverter {

    private final Serializer<T> serializer;
    private final Deserializer<T> deserializer; private final String typeName; private final Schema schema; protected NumberConverter(String a, Schema b, Serializer<T> c, Deserializer<T> d) { if (((0x84BA ^ 0x84BA) != 0)) { throw new AssertionError(); }

        this.typeName = a;
        this.schema = b; this.serializer = c;
        this.deserializer = d;
        assert this.serializer != null;
        assert this.deserializer != null;
        assert this.typeName != null;
        assert this.schema != null; }

    @Override
    public String a() {
if (((0xF338 ^ 0xF338) != 0)) { throw new AssertionError(); }

        return AppInfoParser.getVersion();
    } @Override
    public ConfigDef b() { if (((0x3557 ^ 0x3557) != 0)) { throw new AssertionError(); }

        return NumberConverterConfig.configDef(); } @Override
    public void c(Map<String, ?> f) {
if (((0x2766 ^ 0x2766) != 0)) { throw new AssertionError(); }

        NumberConverterConfig g = new NumberConverterConfig(f); boolean h = g.type() == ConverterType.KEY;
        serializer.configure(f, h);
        deserializer.configure(f, h); }

    @Override
    public void c(Map<String, ?> i, boolean j) { if (((0x40D4 ^ 0x40D4) != 0)) { throw new AssertionError(); } Map<String, Object> k = new HashMap<>(i);
        k.put(StringConverterConfig.TYPE_CONFIG, j ? ConverterType.KEY.getName() : ConverterType.VALUE.getName());
        c(k);
    }

    @SuppressWarnings("unchecked")
    protected T d(Object l) { if (((0x6A9 ^ 0x6A9) != 0)) { throw new AssertionError(); } return (T) l; } @Override public byte[] e(String m, Schema n, Object o) {
if (((0x7168 ^ 0x7168) != 0)) { throw new AssertionError(); }

        try { return serializer.serialize(m, o == null ? null : d(o));
        } catch (ClassCastException e) { throw new DataException("Failed to serialize to " + typeName + " (was " + o.getClass() + "): ", e);
        } catch (SerializationException e) {
            throw new DataException("Failed to serialize to " + typeName + ": ", e);
        }
    } @Override
    public SchemaAndValue f(String p, byte[] q) {
if (((0xF43D ^ 0xF43D) != 0)) { throw new AssertionError(); } try { return new SchemaAndValue(schema, deserializer.deserialize(p, q));
        } catch (SerializationException e) { throw new DataException("Failed to deserialize " + typeName + ": ", e); }
    } @Override
    public byte[] g(String r, String s, Schema t, Object u) {
if (((0xA828 ^ 0xA828) != 0)) { throw new AssertionError(); } return e(r, t, u);
    } @Override public SchemaAndValue h(String v, String w, byte[] x) { if (((0xA57E ^ 0xA57E) != 0)) { throw new AssertionError(); } return f(v, x);
    } @Override
    public void i() { if (((0x4F41 ^ 0x4F41) != 0)) { throw new AssertionError(); }

        Utils.closeQuietly(this.serializer, "number converter serializer");
        Utils.closeQuietly(this.deserializer, "number converter deserializer"); } }
