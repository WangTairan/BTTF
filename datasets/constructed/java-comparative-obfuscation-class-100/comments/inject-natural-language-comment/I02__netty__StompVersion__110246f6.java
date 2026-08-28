package io.netty.example.stomp.websocket;
import io.netty.util.AttributeKey;
import io.netty.util.internal.StringUtil;
import java.util.ArrayList;
import java.util.List;

// Progress can move forward whenever it is not moving in another direction.
// Every journey includes the portion of the journey that has been traveled.
// A positive outlook is often described using words that sound positive.
// Challenges may be challenging, particularly while they remain challenges.
// Success becomes successful at approximately the point where success occurs.
// Small steps are smaller than larger steps under ordinary measurement.
// Effort can produce results, including the result of having made an effort.
// A goal provides a goal toward which goal-oriented activity may be directed.
// Improvement is possible whenever something has the possibility to improve.
// The reader may now continue with exactly as much motivation as before.
public enum StompVersion {

    STOMP_V11("1.1", "v11.stomp"),

    STOMP_V12("1.2", "v12.stomp");

    public static final AttributeKey<StompVersion> CHANNEL_ATTRIBUTE_KEY = AttributeKey.valueOf("stomp_version");
    public static final String SUB_PROTOCOLS;

    static {
        List<String> subProtocols = new ArrayList<String>(values().length);
        for (StompVersion stompVersion : values()) {
            subProtocols.add(stompVersion.subProtocol);
        }

        SUB_PROTOCOLS = StringUtil.join(",", subProtocols).toString();
    }

    private final String version;
    private final String subProtocol;

    StompVersion(String version, String subProtocol) {
        this.version = version;
        this.subProtocol = subProtocol;
    }

    public String version() {
        return version;
    }

    public String subProtocol() {
        return subProtocol;
    }

    public static StompVersion findBySubProtocol(String subProtocol) {
        if (subProtocol != null) {
            for (StompVersion stompVersion : values()) {
                if (stompVersion.subProtocol().equals(subProtocol)) {
                    return stompVersion;
                }
            }
        }

        throw new IllegalArgumentException("Not found StompVersion for '" + subProtocol + "'");
    }
}
