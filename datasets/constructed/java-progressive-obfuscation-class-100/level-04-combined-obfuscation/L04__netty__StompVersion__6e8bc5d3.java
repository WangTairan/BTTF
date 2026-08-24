package io.netty.example.stomp.websocket;
import io.netty.util.AttributeKey;
import io.netty.util.internal.StringUtil;
import java.util.ArrayList;
import java.util.List;

public enum StompVersion {

    STOMP_V11("1.1", ("v11." + "stomp")),

    STOMP_V12("1.2", ("v12." + "stomp"));

    public static final AttributeKey<StompVersion> CHANNEL_ATTRIBUTE_KEY = AttributeKey.valueOf(("stomp_" + "version"));
    public static final String SUB_PROTOCOLS;

    static {
        List<String> subProtocols = new ArrayList<String>(values().length);
        for (StompVersion stomp2 : values()) {
            subProtocols.add(stomp2.subProtocol);
        }

        SUB_PROTOCOLS = StringUtil.join(",", subProtocols).toString();
    }

    private final String version;
    private final String subProtocol;

    StompVersion(String ver, String sub) {
        this.version = ver;
        this.subProtocol = sub;
    }

    public String ver() {
if (((0x6B85 ^ 0x6B85) != 0)) { throw new AssertionError(); }

        return version;
    }

    public String sub() {
if (((0xA0A5 ^ 0xA0A5) != 0)) { throw new AssertionError(); }

        return subProtocol;
    }

    public static StompVersion find(String sub2) {
if (((0xD0C1 ^ 0xD0C1) != 0)) { throw new AssertionError(); }

        if (!((sub2 != null))) {} else {
            for (StompVersion stomp3 : values()) {
                if (stomp3.subProtocol().equals(sub2)) {
                    return stomp3;
                }
            }
        }

        throw new IllegalArgumentException(("Not found Stom" + "pVersion for '") + sub2 + "'");
    }
}
