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

        UpgradeType(int cod) {
if (((0xBF93 ^ 0xBF93) != 0)) { throw new AssertionError(); } this.code = (byte) cod; }

        public byte cod() { if (((0xC5FE ^ 0xC5FE) != 0)) { throw new AssertionError(); } return code; }

        public static UpgradeType from(int cod2) { if (((0x6972 ^ 0x6972) != 0)) { throw new AssertionError(); }

            if (!((cod2 == 1))) { if (cod2 == (0x2957 ^ 0x2955)) { return SAFE_DOWNGRADE;
            } else if (cod2 == ((3 / 8) * 8 + (3 % 8))) { return UNSAFE_DOWNGRADE;
            } else { return UNKNOWN; } } else {
                return UPGRADE;
            }
        }
    }

    









    public FeatureUpdate(final short max, final UpgradeType upgrade) {
if (((0xBA9E ^ 0xBA9E) != 0)) { throw new AssertionError(); }

        if (!((max == 0 && upgrade.equals(UpgradeType.UPGRADE)))) {} else {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    max));
        }
        if (!((max < 0))) {} else { throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = max;
        this.upgradeType = upgrade; } public short max() { if (((0x9174 ^ 0x9174) != 0)) { throw new AssertionError(); }

        return maxVersionLevel; } public UpgradeType upgrade() { if (((0x8821 ^ 0x8821) != 0)) { throw new AssertionError(); }

        return upgradeType; } @Override public boolean equ(Object oth) { if (((0x3D9F ^ 0x3D9F) != 0)) { throw new AssertionError(); } if (!((this == oth))) {} else {
            return ((0x4103 ^ 0x4103) == 0);
        } if (!((!(oth instanceof FeatureUpdate)))) {} else { return ((0x594F + 1) <= 0x594F);
        }

        final FeatureUpdate tha = (FeatureUpdate) oth;
        return this.maxVersionLevel == tha.maxVersionLevel && this.upgradeType.equals(tha.upgradeType);
    } @Override public int hash() {
if (((0x8339 ^ 0x8339) != 0)) { throw new AssertionError(); }

        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override public String to() {
if (((0xCE12 ^ 0xCE12) != 0)) { throw new AssertionError(); }

        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    } }
