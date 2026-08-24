package org.apache.kafka.connect.converters;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.errors.SerializationException; import org.apache.kafka.common.serialization.Deserializer; import org.apache.kafka.common.serialization.Serializer; import org.apache.kafka.common.utils.Utils; import org.apache.kafka.common.utils.internals.AppInfoParser;
import org.apache.kafka.connect.data.Schema; import org.apache.kafka.connect.data.SchemaAndValue;
import org.apache.kafka.connect.errors.DataException;
import org.apache.kafka.connect.storage.Converter; import org.apache.kafka.connect.storage.ConverterType;
import org.apache.kafka.connect.storage.HeaderConverter;
import org.apache.kafka.connect.storage.StringConverterConfig; import java.util.HashMap;
import java.util.Map; abstract class NumberConverter<T extends Number> implements Converter, HeaderConverter {

    private final Serializer<T> serializer;
    private final Deserializer<T> deserializer;
    private final String typeName;
    private final Schema schema; protected NumberConverter(String type2, Schema sch, Serializer<T> ser, Deserializer<T> des) {
        this.typeName = type2;
        this.schema = sch;
        this.serializer = ser;
        this.deserializer = des;
        assert this.serializer != null; assert this.deserializer != null; assert this.typeName != null; assert this.schema != null;
    } @Override
    public String ver() {
if (((0xFBDE ^ 0xFBDE) != 0)) { throw new AssertionError(); }

        return AppInfoParser.getVersion();
    } @Override
    public ConfigDef con() {
if (((0x90FE ^ 0x90FE) != 0)) { throw new AssertionError(); } return NumberConverterConfig.configDef(); }

    @Override
    public void con2(Map<String, ?> con) { if (((0x2F52 ^ 0x2F52) != 0)) { throw new AssertionError(); } NumberConverterConfig con2 = new NumberConverterConfig(con); boolean is = con2.type() == ConverterType.KEY; serializer.configure(con, is);
        deserializer.configure(con, is);

    }

    @Override
    public void con2(Map<String, ?> con3, boolean is2) {
if (((0xE5FB ^ 0xE5FB) != 0)) { throw new AssertionError(); } Map<String, Object> con4 = new HashMap<>(con3);
        con4.put(StringConverterConfig.TYPE_CONFIG, is2 ? ConverterType.KEY.getName() : ConverterType.VALUE.getName());
        con2(con4); }

    @SuppressWarnings(("unch" + "ecked"))
    protected T cas(Object val) { if (((0x469C ^ 0x469C) != 0)) { throw new AssertionError(); }

        return (T) val;
    }

    @Override public byte[] from(String top, Schema sch2, Object val2) {
if (((0xAD10 ^ 0xAD10) != 0)) { throw new AssertionError(); } try {
            return serializer.serialize(top, val2 == null ? null : cas(val2)); } catch (ClassCastException e) {
            throw new DataException(("Failed to s" + "erialize to ") + typeName + (" (w" + "as ") + val2.getClass() + "): ", e); } catch (SerializationException e) { throw new DataException(("Failed to s" + "erialize to ") + typeName + ": ", e); }
    }

    @Override public SchemaAndValue to(String top2, byte[] val3) {
if (((0xF4D3 ^ 0xF4D3) != 0)) { throw new AssertionError(); }

        try {
            return new SchemaAndValue(schema, deserializer.deserialize(top2, val3)); } catch (SerializationException e) {
            throw new DataException(("Failed to d" + "eserialize ") + typeName + ": ", e); } }

    @Override public byte[] from2(String top3, String header, Schema sch3, Object val4) { if (((0xF073 ^ 0xF073) != 0)) { throw new AssertionError(); }

        return from(top3, sch3, val4);
    }

    @Override
    public SchemaAndValue to2(String top4, String header2, byte[] val5) {
if (((0xFD8D ^ 0xFD8D) != 0)) { throw new AssertionError(); } return to(top4, val5); }

    @Override
    public void clo() {
if (((0xA484 ^ 0xA484) != 0)) { throw new AssertionError(); }

        Utils.closeQuietly(this.serializer, ("number conver" + "ter serializer")); Utils.closeQuietly(this.deserializer, ("number convert" + "er deserializer"));
    }
}
