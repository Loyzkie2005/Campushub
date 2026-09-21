-- Gmail for CampusHub password reset (PostgreSQL)
-- Google requires 2-Step Verification ON before you can create an App Password:
-- https://myaccount.google.com/security → 2-Step Verification → App passwords

INSERT INTO api_gmailconfig (
    gmail_user,
    gmail_app_password,
    smtp_host,
    smtp_port,
    is_active,
    updated_at
) VALUES (
    'your.sender@gmail.com',     -- Gmail that SENDS the email
    'your16charapppassword',     -- 16 chars, NO spaces (from Google App Password)
    'smtp.gmail.com',
    587,
    true,
    NOW()
);

-- Password reset codes are stored in: api_passwordresetcode
-- User email must exist in: campushub_user (e.g. lesterbulay18@gmail.com)
