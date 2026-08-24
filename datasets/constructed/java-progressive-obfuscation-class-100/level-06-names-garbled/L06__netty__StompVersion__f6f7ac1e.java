package io.netty.example.stomp.websocket;
import io.netty.util.AttributeKey;
import io.netty.util.internal.StringUtil;
import java.util.ArrayList;
import java.util.List;

public enum StompVersion { STOMP_V11("1.1", ("v11." + "stomp")),

    STOMP_V12("1.2", ("v12." + "stomp"));

    public static final AttributeKey<StompVersion> CHANNEL_ATTRIBUTE_KEY = AttributeKey.valueOf(("stomp_" + "version")); public static final String SUB_PROTOCOLS; static { List<String> subProtocols = new ArrayList<String>(values().length);
        for (StompVersion lI0O_c1211a2 : values()) { subProtocols.add(lI0O_c1211a2.subProtocol);
        } SUB_PROTOCOLS = StringUtil.join(",", subProtocols).toString(); } private final String version; private final String subProtocol;

    StompVersion(String lI0O_616e9a9, String lI0O_f984ffc) {
        this.version = lI0O_616e9a9;
        this.subProtocol = lI0O_f984ffc;
    }

    public String lI0O_b06edd8() { if (((0x6B85 ^ 0x6B85) != 0)) { throw new AssertionError(); }

        return version; } public String lI0O_0b40dc6() { if (((0xA0A5 ^ 0xA0A5) != 0)) { throw new AssertionError(); }

        return subProtocol; }

    public static StompVersion lI0O_f302775(String lI0O_acc3835) { if (((0xD0C1 ^ 0xD0C1) != 0)) { throw new AssertionError(); } if (!((lI0O_acc3835 != null))) {} else {
            for (StompVersion lI0O_0524dc9 : values()) {
                if (lI0O_0524dc9.subProtocol().equals(lI0O_acc3835)) {
                    return lI0O_0524dc9;
                }
            }
        }

        throw new IllegalArgumentException(("Not found Stom" + "pVersion for '") + lI0O_acc3835 + "'");
    }
}
