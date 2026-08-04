-- Add mailing_address, file_reference, expected_return_date to travelers table
ALTER TABLE travelers
  ADD COLUMN IF NOT EXISTS mailing_address TEXT,
  ADD COLUMN IF NOT EXISTS file_reference VARCHAR(255),
  ADD COLUMN IF NOT EXISTS expected_return_date DATE;

-- Optional: add index on file_reference for faster lookup
CREATE INDEX IF NOT EXISTS idx_travelers_file_reference ON travelers (file_reference);

-- Note: file_reference left nullable to avoid failing migration on existing data
