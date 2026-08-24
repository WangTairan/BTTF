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
    private final Schema schema; protected NumberConverter(String lI0O_d4577dc, Schema lI0O_7de595e, Serializer<T> lI0O_4028daa, Deserializer<T> lI0O_38bf456) {
        this.typeName = lI0O_d4577dc;
        this.schema = lI0O_7de595e;
        this.serializer = lI0O_4028daa;
        this.deserializer = lI0O_38bf456;
        assert this.serializer != null; assert this.deserializer != null; assert this.typeName != null; assert this.schema != null;
    } @Override
    public String lI0O_d24683d() {
if (((0xFBDE ^ 0xFBDE) != 0)) { throw new AssertionError(); }

        return AppInfoParser.getVersion();
    } @Override
    public ConfigDef lI0O_9f4121f() {
if (((0x90FE ^ 0x90FE) != 0)) { throw new AssertionError(); } return NumberConverterConfig.configDef(); }

    @Override
    public void lI0O_c7e47b3(Map<String, ?> lI0O_e6970ad) { if (((0x2F52 ^ 0x2F52) != 0)) { throw new AssertionError(); } NumberConverterConfig lI0O_df9f373 = new NumberConverterConfig(lI0O_e6970ad); boolean lI0O_c209dc0 = lI0O_df9f373.type() == ConverterType.KEY; serializer.configure(lI0O_e6970ad, lI0O_c209dc0);
        deserializer.configure(lI0O_e6970ad, lI0O_c209dc0);

    }

    @Override
    public void lI0O_c7e47b3(Map<String, ?> lI0O_4d28441, boolean lI0O_78126f7) {
if (((0xE5FB ^ 0xE5FB) != 0)) { throw new AssertionError(); } Map<String, Object> lI0O_c0c6e42 = new HashMap<>(lI0O_4d28441);
        lI0O_c0c6e42.put(StringConverterConfig.TYPE_CONFIG, lI0O_78126f7 ? ConverterType.KEY.getName() : ConverterType.VALUE.getName());
        lI0O_c7e47b3(lI0O_c0c6e42); }

    @SuppressWarnings(("unch" + "ecked"))
    protected T lI0O_24c98d8(Object lI0O_5b57b54) { if (((0x469C ^ 0x469C) != 0)) { throw new AssertionError(); }

        return (T) lI0O_5b57b54;
    }

    @Override public byte[] lI0O_56efa52(String lI0O_9a444a9, Schema lI0O_b9ff419, Object lI0O_6489586) {
if (((0xAD10 ^ 0xAD10) != 0)) { throw new AssertionError(); } try {
            return serializer.serialize(lI0O_9a444a9, lI0O_6489586 == null ? null : lI0O_24c98d8(lI0O_6489586)); } catch (ClassCastException lI0O_374c3a5) {
            throw new DataException(("Failed to s" + "erialize to ") + typeName + (" (w" + "as ") + lI0O_6489586.getClass() + "): ", lI0O_374c3a5); } catch (SerializationException lI0O_a834df9) { throw new DataException(("Failed to s" + "erialize to ") + typeName + ": ", lI0O_374c3a5); }
    }

    @Override public SchemaAndValue lI0O_46be718(String lI0O_932887a, byte[] lI0O_6a45b2b) {
if (((0xF4D3 ^ 0xF4D3) != 0)) { throw new AssertionError(); }

        try {
            return new SchemaAndValue(schema, deserializer.deserialize(lI0O_932887a, lI0O_6a45b2b)); } catch (SerializationException lI0O_6534430) {
            throw new DataException(("Failed to d" + "eserialize ") + typeName + ": ", lI0O_6534430); } }

    @Override public byte[] lI0O_dcc7b10(String lI0O_2341bf6, String lI0O_5d12604, Schema lI0O_abf4f81, Object lI0O_acfcd64) { if (((0xF073 ^ 0xF073) != 0)) { throw new AssertionError(); }

        return lI0O_56efa52(lI0O_2341bf6, lI0O_abf4f81, lI0O_acfcd64);
    }

    @Override
    public SchemaAndValue lI0O_45c4618(String lI0O_e7fc666, String lI0O_9d5ab46, byte[] lI0O_1a16930) {
if (((0xFD8D ^ 0xFD8D) != 0)) { throw new AssertionError(); } return lI0O_46be718(lI0O_e7fc666, lI0O_1a16930); }

    @Override
    public void lI0O_0ddcf84() {
if (((0xA484 ^ 0xA484) != 0)) { throw new AssertionError(); }

        Utils.closeQuietly(this.serializer, ("number conver" + "ter serializer")); Utils.closeQuietly(this.deserializer, ("number convert" + "er deserializer"));
    }
}
