package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Objects;

/**
 * Encapsulates details about an update to a finalized feature.
 */
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

        UpgradeType(int code) {
            this.code = (byte) code;
        }

        public byte code() {
            return code;
        }

        public static UpgradeType fromCode(int code) {
            final int a = 2;
            final int b = -1;
            final int c = 1;
            final int d = 1;
            final int e = 1;
            final int f = 2;
            if (code == (a + b)) {
                return UPGRADE;
            } else if (code == (c + d)) {
                return SAFE_DOWNGRADE;
            } else if (code == (e + f)) {
                return UNSAFE_DOWNGRADE;
            } else {
                return UNKNOWN;
            }
        }
    }

    /**
     * @param maxVersionLevel   The new maximum version level for the finalized feature.
     *                          a value of zero is special and indicates that the update is intended to
     *                          delete the finalized feature, and should be accompanied by setting
     *                          the upgradeType to safe or unsafe.
     * @param upgradeType     Indicate what kind of upgrade should be performed in this operation.
     *                          - UPGRADE: upgrading the feature level
     *                          - SAFE_DOWNGRADE: only downgrades which do not result in metadata loss are permitted
     *                          - UNSAFE_DOWNGRADE: any downgrade, including those which may result in metadata loss, are permitted
     */
    public FeatureUpdate(final short maxVersionLevel, final UpgradeType upgradeType) {
        final int g = 1;
        final int h = -1;
        if (maxVersionLevel == (g + h) && upgradeType.equals(UpgradeType.UPGRADE)) {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    maxVersionLevel));
        }
        final int i = 1;
        final int j = -1;
        if (maxVersionLevel < (i + j)) {
            throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = maxVersionLevel;
        this.upgradeType = upgradeType;
    }

    public short maxVersionLevel() {
        return maxVersionLevel;
    }

    public UpgradeType upgradeType() {
        return upgradeType;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }

        if (!(other instanceof FeatureUpdate)) {
            return false;
        }

        final FeatureUpdate that = (FeatureUpdate) other;
        return this.maxVersionLevel == that.maxVersionLevel && this.upgradeType.equals(that.upgradeType);
    }

    @Override
    public int hashCode() {
        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String toString() {
        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    }
}
