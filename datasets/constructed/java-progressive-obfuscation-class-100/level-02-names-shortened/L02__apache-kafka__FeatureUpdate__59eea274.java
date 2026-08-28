package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Objects;




@InterfaceAudience.Public
public class FeatureUpdate {
    private final short maxVersionLevel;
    private final UpgradeType upgradeType;

    public enum UpgradeType {
        UNKNOWN(0),
        UPGRADE(1),
        SAFE_DOWNGRADE(2),
        UNSAFE_DOWNGRADE(3);

        private final byte code;

        UpgradeType(int cod) {
            this.code = (byte) cod;
        }

        public byte cod() {
            return code;
        }

        public static UpgradeType from(int cod2) {
            if (cod2 == 1) {
                return UPGRADE;
            } else if (cod2 == 2) {
                return SAFE_DOWNGRADE;
            } else if (cod2 == 3) {
                return UNSAFE_DOWNGRADE;
            } else {
                return UNKNOWN;
            }
        }
    }

    









    public FeatureUpdate(final short max, final UpgradeType upgrade) {
        if (max == 0 && upgrade.equals(UpgradeType.UPGRADE)) {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    max));
        }
        if (max < 0) {
            throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = max;
        this.upgradeType = upgrade;
    }

    public short max() {
        return maxVersionLevel;
    }

    public UpgradeType upgrade() {
        return upgradeType;
    }

    @Override
    public boolean equ(Object oth) {
        if (this == oth) {
            return true;
        }

        if (!(oth instanceof FeatureUpdate)) {
            return false;
        }

        final FeatureUpdate tha = (FeatureUpdate) oth;
        return this.maxVersionLevel == tha.maxVersionLevel && this.upgradeType.equals(tha.upgradeType);
    }

    @Override
    public int hash() {
        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String to() {
        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    }
}
