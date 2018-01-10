const TRANSITION_CORE_LINK = 1;
const TRANSITION_CORE_TYPED = 2;
const TRANSITION_CORE_AUTO_BOOKMARK = 3;
const TRANSITION_CORE_AUTO_SUBFRAME = 3;
const TRANSITION_CORE_MANUAL_SUBFRAME = 4;
const TRANSITION_CORE_GENERATED = 5;
const TRANSITION_CORE_START_PAGE = 6;
const TRANSITION_CORE_FORM_SUBMIT = 7;
const TRANSITION_CORE_RELOAD = 8;
const TRANSITION_CORE_KEYWORD = 9;
const TRANSITION_CORE_KEYWORD_GENERATED = 10;
const TRANSITION_CORE_MASK = 0xFF;

const TRANSITION_QUAL_BLOCKED = 0x00800000;
const TRANSITION_QUAL_FORWARD_BACK = 0x01000000;
const TRANSITION_QUAL_FROM_ADDRESS_BAR = 0x02000000;
const TRANSITION_QUAL_HOME_PAGE = 0x04000000;
const TRANSITION_QUAL_FROM_API = 0x08000000;
const TRANSITION_QUAL_CHAIN_START = 0x10000000;
const TRANSITION_QUAL_CHAIN_END = 0x20000000;
const TRANSITION_QUAL_CLIENT_REDIRECT = 0x40000000;
const TRANSITION_QUAL_SERVER_REDIRECT = 0x80000000;
const TRANSITION_QUAL_IS_REDIRECT_MASK = 0xC0000000;
const TRANSITION_QUAL_MASK = 0xFFFFFF00;

function flagSet(mask, flag) {
    // Javascript converts operands of bitwise operations to signed 32-bit integers.
    // We need unsigned. >>> 0 makes it unsigned again.
    return ((mask & flag) >>> 0) === flag;
}

function displayTransitionCore(transition) {
    const newTransition = transition & TRANSITION_CORE_MASK;
    switch (newTransition) {
        case TRANSITION_CORE_LINK:
            return "LINK";
        case TRANSITION_CORE_TYPED:
            return "TYPED";
        case TRANSITION_CORE_AUTO_BOOKMARK:
            return "AUTO_BOOKMARK";
        case TRANSITION_CORE_AUTO_SUBFRAME:
            return "AUTO_SUBFRAME";
        case TRANSITION_CORE_MANUAL_SUBFRAME:
            return "MANUAL_SUBFRAME";
        case TRANSITION_CORE_GENERATED:
            return "GENERATED";
        case TRANSITION_CORE_START_PAGE:
            return "START_PAGE";
        case TRANSITION_CORE_FORM_SUBMIT:
            return "FORM_SUBMIT";
        case TRANSITION_CORE_RELOAD:
            return "RELOAD";
        case TRANSITION_CORE_KEYWORD:
            return "KEYWORD";
        case TRANSITION_CORE_KEYWORD_GENERATED:
            return "GENERATED";
        default:
            return "UNKNOWN";
    }
}

function displayTransitionQualifier(transistion) {
    const masked = (transistion & TRANSITION_QUAL_MASK) >>> 0;
    const flags = [];

    if (flagSet(masked, TRANSITION_QUAL_BLOCKED)) {
        flags.push("BLOCKED");
    }
    if (flagSet(masked, TRANSITION_QUAL_FORWARD_BACK)) {
        flags.push("FORWARD_BACK");
    }
    if (flagSet(masked, TRANSITION_QUAL_FROM_ADDRESS_BAR)) {
        flags.push("FROM_ADDRESS_BAR");
    }
    if (flagSet(masked, TRANSITION_QUAL_HOME_PAGE)) {
        flags.push("HOME_PAGE");
    }
    if (flagSet(masked, TRANSITION_QUAL_FROM_API)) {
        flags.push("FROM_API");
    }
    if (flagSet(masked, TRANSITION_QUAL_CHAIN_START)) {
        flags.push("CHAIN_START");
    }
    if (flagSet(masked, TRANSITION_QUAL_CHAIN_END)) {
        flags.push("CHAIN_END");
    }

    if (((masked & TRANSITION_QUAL_IS_REDIRECT_MASK) >>> 0) !== 0x00) {
        flags.push("REDIRECT");
    }

    if (flagSet(masked, TRANSITION_QUAL_CLIENT_REDIRECT)) {
        flags.push("CLIENT_REDIRECT");
    }
    if (flagSet(masked, TRANSITION_QUAL_SERVER_REDIRECT)) {
        flags.push("SERVER_REDIRECT");
    }

    if (flags.length > 0) {
        return flags.join("|");
    }
    return "NONE";
}

const VISIT_SOURCE_SYNC = 0;
const VISIT_SOURCE_BROWSED = 1;
const VISIT_SOURCE_EXTENSION = 2;
const VISIT_SOURCE_FIREFOX_IMPORTED = 3;
const VISIT_SOURCE_IE_IMPORTED = 4;
const VISIT_SOURCE_SAFARI_IMPORTED = 5;

function displayVisitSource(source) {
    switch (source) {
        case VISIT_SOURCE_SYNC:
            return "SYNCED";
        case VISIT_SOURCE_BROWSED:
            return "BROWSED";
        case VISIT_SOURCE_EXTENSION:
            return "EXTENSION";
        case VISIT_SOURCE_FIREFOX_IMPORTED:
            return "FIREFOX";
        case VISIT_SOURCE_IE_IMPORTED:
            return "IE";
        case VISIT_SOURCE_SAFARI_IMPORTED:
            return "SAFARI";
        default:
            return "UNKNOWN";
    }
}