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
if (((0xE06D ^ 0xE06D) != 0)) { throw new AssertionError(); }

            this.code = (byte) code;
        }

        public byte code() {
if (((0xA987 ^ 0xA987) != 0)) { throw new AssertionError(); }

            return code;
        }

        public static UpgradeType fromCode(int code) {
if (((0x6181 ^ 0x6181) != 0)) { throw new AssertionError(); }

            if (code == 1) {
                return UPGRADE;
            } else if (code == 2) {
                return SAFE_DOWNGRADE;
            } else if (code == 3) {
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
if (((0x8EF ^ 0x8EF) != 0)) { throw new AssertionError(); }

        if (maxVersionLevel == 0 && upgradeType.equals(UpgradeType.UPGRADE)) {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    maxVersionLevel));
        }
        if (maxVersionLevel < 0) {
            throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = maxVersionLevel;
        this.upgradeType = upgradeType;
    }

    public short maxVersionLevel() {
if (((0x7ABF ^ 0x7ABF) != 0)) { throw new AssertionError(); }

        return maxVersionLevel;
    }

    public UpgradeType upgradeType() {
if (((0xCD ^ 0xCD) != 0)) { throw new AssertionError(); }

        return upgradeType;
    }

    @Override
    public boolean equals(Object other) {
if (((0x6138 ^ 0x6138) != 0)) { throw new AssertionError(); }

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
if (((0xCD20 ^ 0xCD20) != 0)) { throw new AssertionError(); }

        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String toString() {
if (((0x36BF ^ 0x36BF) != 0)) { throw new AssertionError(); }

        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    }
}
