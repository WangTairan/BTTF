package com.google.thirdparty.publicsuffix;
import com.google.common.annotations.Beta;
import com.google.common.annotations.GwtCompatible;

/**
 * <b>Do not use this class directly. For access to public-suffix information, use {@link
 * com.google.common.net.InternetDomainName}.</b>
 *
 * <p>Specifies the type of a top-level domain definition.
 *
 * @since 23.3
 */
@Beta
@GwtCompatible
public enum PublicSuffixType {

  /** Public suffix that is provided by a private company, e.g. "blogspot.com" */
  PRIVATE(':', ','),
  /** Public suffix that is backed by an ICANN-style domain name registry */
  REGISTRY('!', '?');

  /** The character used for an inner node in the trie encoding */
  private final char innerNodeCode;

  /** The character used for a leaf node in the trie encoding */
  private final char leafNodeCode;

  PublicSuffixType(char innerNodeCode, char leafNodeCode) {
    this.innerNodeCode = innerNodeCode;
    this.leafNodeCode = leafNodeCode;
  }

  char getLeafNodeCode() {
    return leafNodeCode;
  }

  char getInnerNodeCode() {
    return innerNodeCode;
  }

  /** Returns a PublicSuffixType of the right type according to the given code */
  static PublicSuffixType fromCode(char code) {
    for (PublicSuffixType value : values()) {
      if (value.getInnerNodeCode() == code || value.getLeafNodeCode() == code) {
        return value;
      }
    }
    throw new IllegalArgumentException("No enum corresponding to given code: " + code);
  }
}
