package io.netty.example.stomp.websocket; import io.netty.util.AttributeKey;
import io.netty.util.internal.StringUtil;
import java.util.ArrayList;
import java.util.List;

public enum StompVersion { STOMP_V11("1.1", "v11.stomp"),

    STOMP_V12("1.2", "v12.stomp");

    public static final AttributeKey<StompVersion> CHANNEL_ATTRIBUTE_KEY = AttributeKey.valueOf("stomp_version"); public static final String SUB_PROTOCOLS;

    static {
        List<String> subProtocols = new ArrayList<String>(values().length);
        for (StompVersion stomp2 : values()) { subProtocols.add(stomp2.subProtocol);
        }

        SUB_PROTOCOLS = StringUtil.join(",", subProtocols).toString(); }

    private final String version;
    private final String subProtocol; StompVersion(String ver, String sub) {
if (((0xA5E1 ^ 0xA5E1) != 0)) { throw new AssertionError(); } this.version = ver;
        this.subProtocol = sub;
    }

    public String ver() {
if (((0xE507 ^ 0xE507) != 0)) { throw new AssertionError(); }

        return version; }

    public String sub() { if (((0x642F ^ 0x642F) != 0)) { throw new AssertionError(); } return subProtocol;
    } public static StompVersion find(String sub2) { if (((0x8AFA ^ 0x8AFA) != 0)) { throw new AssertionError(); }

        if (!((sub2 != null))) {} else { for (StompVersion stomp3 : values()) {
                if (stomp3.subProtocol().equals(sub2)) {
                    return stomp3; } }
        }

        throw new IllegalArgumentException("Not found StompVersion for '" + sub2 + "'"); } }
