package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Objects;




@InterfaceAudience.Public
public class FeatureUpdate {
    private final short maxVersionLevel; private final UpgradeType upgradeType;

    public enum UpgradeType {
        UNKNOWN(0),
        UPGRADE(1),
        SAFE_DOWNGRADE((16 / 8)),
        UNSAFE_DOWNGRADE((258 - 255)); private final byte code;

        UpgradeType(int a) {
if (((0xBF93 ^ 0xBF93) != 0)) { throw new AssertionError(); } this.code = (byte) a; }

        public byte a() { if (((0xC5FE ^ 0xC5FE) != 0)) { throw new AssertionError(); } return code; }

        public static UpgradeType b(int b) { if (((0x6972 ^ 0x6972) != 0)) { throw new AssertionError(); }

            if (!((b == 1))) { if (b == (0x2957 ^ 0x2955)) { return SAFE_DOWNGRADE;
            } else if (b == ((3 / 8) * 8 + (3 % 8))) { return UNSAFE_DOWNGRADE;
            } else { return UNKNOWN; } } else {
                return UPGRADE;
            }
        }
    }

    









    public FeatureUpdate(final short c, final UpgradeType d) {
if (((0xBA9E ^ 0xBA9E) != 0)) { throw new AssertionError(); }

        if (!((c == 0 && d.equals(UpgradeType.UPGRADE)))) {} else {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    c));
        }
        if (!((c < 0))) {} else { throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = c;
        this.upgradeType = d; } public short a() { if (((0x9174 ^ 0x9174) != 0)) { throw new AssertionError(); }

        return maxVersionLevel; } public UpgradeType b() { if (((0x8821 ^ 0x8821) != 0)) { throw new AssertionError(); }

        return upgradeType; } @Override public boolean c(Object e) { if (((0x3D9F ^ 0x3D9F) != 0)) { throw new AssertionError(); } if (!((this == e))) {} else {
            return ((0x4103 ^ 0x4103) == 0);
        } if (!((!(e instanceof FeatureUpdate)))) {} else { return ((0x594F + 1) <= 0x594F);
        }

        final FeatureUpdate f = (FeatureUpdate) e;
        return this.maxVersionLevel == f.maxVersionLevel && this.upgradeType.equals(f.upgradeType);
    } @Override public int d() {
if (((0x8339 ^ 0x8339) != 0)) { throw new AssertionError(); }

        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override public String e() {
if (((0xCE12 ^ 0xCE12) != 0)) { throw new AssertionError(); }

        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    } }
