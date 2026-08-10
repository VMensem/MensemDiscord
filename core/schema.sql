-- Users and Profiles (Unified)
CREATE TABLE IF NOT EXISTS users (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    balance BIGINT DEFAULT 0,
    bank BIGINT DEFAULT 0,
    xp BIGINT DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_xp DOUBLE PRECISION DEFAULT 0,
    reputation INTEGER DEFAULT 0,
    messages BIGINT DEFAULT 0,
    voice_seconds BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Economy
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    type VARCHAR(50),
    amount BIGINT,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shop_items (
    item_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price BIGINT NOT NULL,
    type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id INTEGER REFERENCES shop_items(item_id),
    amount INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cooldowns (
    cooldown_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Guild Settings
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    log_channels JSONB,
    ticket_category_id BIGINT,
    ticket_log_channel_id BIGINT,
    staff_role_ids BIGINT[],
    embed_color VARCHAR(10),
    economy_settings JSONB,
    leveling_settings JSONB,
    clan_settings JSONB,
    event_settings JSONB,
    moderation_settings JSONB,
    verify_settings JSONB
);

-- Clans
CREATE TABLE IF NOT EXISTS clans (
    clan_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    tag VARCHAR(10) NOT NULL UNIQUE,
    description TEXT,
    leader_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role_id BIGINT,
    category_id BIGINT,
    chat_channel_id BIGINT,
    voice_channel_id BIGINT,
    balance BIGINT DEFAULT 0,
    level INTEGER DEFAULT 1,
    xp BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INTEGER REFERENCES clans(clan_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (clan_id, user_id)
);

CREATE TABLE IF NOT EXISTS clan_invites (
    invite_id SERIAL PRIMARY KEY,
    clan_id INTEGER REFERENCES clans(clan_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clan_history (
    history_id SERIAL PRIMARY KEY,
    clan_id INTEGER REFERENCES clans(clan_id) ON DELETE CASCADE,
    action TEXT,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clan_wars (
    war_id SERIAL PRIMARY KEY,
    clan_one INTEGER REFERENCES clans(clan_id) ON DELETE CASCADE,
    clan_two INTEGER REFERENCES clans(clan_id) ON DELETE CASCADE,
    status VARCHAR(20),
    winner INTEGER REFERENCES clans(clan_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tickets
CREATE TABLE IF NOT EXISTS ticket_panels (
    panel_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT,
    message_id BIGINT,
    title TEXT,
    description TEXT,
    color INTEGER
);

CREATE TABLE IF NOT EXISTS ticket_categories (
    category_id SERIAL PRIMARY KEY,
    panel_id INTEGER REFERENCES ticket_panels(panel_id) ON DELETE CASCADE,
    name TEXT,
    description TEXT,
    emoji TEXT,
    target_category_id BIGINT,
    staff_role_id BIGINT
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    category_id INTEGER REFERENCES ticket_categories(category_id),
    status VARCHAR(20) DEFAULT 'open',
    claimed_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    event_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    max_participants INTEGER,
    reward TEXT,
    game TEXT,
    state VARCHAR(20) DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS event_participants (
    event_id INTEGER REFERENCES events(event_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, user_id)
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    report_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    target_id BIGINT,
    channel_id BIGINT,
    reason TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT '🟡 Open',
    moderator_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_history (
    history_id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(report_id) ON DELETE CASCADE,
    action TEXT,
    actor_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Moderation
CREATE TABLE IF NOT EXISTS moderation_cases (
    case_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    mod_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_warnings (
    warning_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    case_id INTEGER REFERENCES moderation_cases(case_id) ON DELETE CASCADE,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS moderation_notes (
    note_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_case_edits (
    edit_id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES moderation_cases(case_id) ON DELETE CASCADE,
    mod_id BIGINT NOT NULL,
    field TEXT,
    old_val TEXT,
    new_val TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Staff
CREATE TABLE IF NOT EXISTS staff_applications (
    application_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    position TEXT NOT NULL,
    answers JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reviewer_id BIGINT,
    rejection_reason TEXT,
    channel_id BIGINT,
    message_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE
);

-- Voice
CREATE TABLE IF NOT EXISTS voice_rooms (
    room_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL UNIQUE,
    owner_id BIGINT NOT NULL,
    room_type TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    panel_channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_personal_rooms (
    personal_room_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL UNIQUE,
    channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_couples (
    couple_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Verify Stats
CREATE TABLE IF NOT EXISTS verify_voice_totals (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    seconds BIGINT DEFAULT 0,
    PRIMARY KEY (guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_support_daily (
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    seconds BIGINT DEFAULT 0,
    PRIMARY KEY (day, guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_active_voice (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_daily_reports (
    day DATE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS verify_support_actions (
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    verified INTEGER DEFAULT 0,
    no_access INTEGER DEFAULT 0,
    PRIMARY KEY (day, guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_support_reviews (
    review_id SERIAL PRIMARY KEY,
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    reviewer_name TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Suggestions
CREATE TABLE IF NOT EXISTS suggestions (
    suggestion_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    message_id BIGINT,
    author_id BIGINT NOT NULL,
    channel_id BIGINT,
    title TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT '🟡 На рассмотрении',
    comment TEXT,
    admin_id BIGINT,
    votes_up BIGINT[],
    votes_down BIGINT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suggestion_config (
    guild_id BIGINT NOT NULL,
    key VARCHAR(50) NOT NULL,
    value BIGINT,
    PRIMARY KEY (guild_id, key)
);

-- Embed Templates
CREATE TABLE IF NOT EXISTS message_templates (
    template_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    json_data JSONB NOT NULL
);

-- Reaction Roles
CREATE TABLE IF NOT EXISTS reaction_roles (
    guild_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    emoji TEXT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, message_id, emoji)
);

-- AI Assistant
CREATE TABLE IF NOT EXISTS ai_history (
    message_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_ratelimits (
    user_id BIGINT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_config (
    guild_id BIGINT NOT NULL,
    key VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (guild_id, key)
);

-- Personal Roles Listings
CREATE TABLE IF NOT EXISTS personal_role_listings (
    listing_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    seller_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    price BIGINT NOT NULL,
    is_sold BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
