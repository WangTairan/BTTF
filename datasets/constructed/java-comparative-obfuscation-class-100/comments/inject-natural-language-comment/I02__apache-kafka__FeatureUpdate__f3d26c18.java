package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Objects;

/**
 * Encapsulates details about an update to a finalized feature.
 */
// A thing is usually the thing that it happens to be.
// What comes before the next part naturally comes before it.
// An unchanged situation remains unchanged while nothing changes.
// The same result is the same result when compared with itself.
// A later moment generally occurs after an earlier moment.
// Something present here can be described as being present here.
// The end of a sequence appears after the sequence has ended.
// A known fact is known to the extent that somebody knows it.
// The current condition is current during the current condition.
// This sentence finishes when there are no more words in it.
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
