--
-- PostgreSQL database dump
--


-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: assignmentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assignmentstatus AS ENUM (
    'assigned',
    'in_progress',
    'passed',
    'failed'
);


--
-- Name: attemptstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.attemptstatus AS ENUM (
    'in_progress',
    'completed',
    'timed_out'
);


--
-- Name: batchstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.batchstatus AS ENUM (
    'draft',
    'processing',
    'completed',
    'archived'
);


--
-- Name: checktype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.checktype AS ENUM (
    'primary',
    'periodic',
    'repeat',
    'unplanned'
);


--
-- Name: commissionrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.commissionrole AS ENUM (
    'chair',
    'member'
);


--
-- Name: importrowstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.importrowstatus AS ENUM (
    'ok',
    'manual_review',
    'duplicate',
    'error'
);


--
-- Name: materialtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.materialtype AS ENUM (
    'video_file',
    'video_url',
    'pdf',
    'docx',
    'image',
    'external_link'
);


--
-- Name: participantresult; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.participantresult AS ENUM (
    'passed',
    'failed'
);


--
-- Name: protocolstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.protocolstatus AS ENUM (
    'draft',
    'awaiting_signatures',
    'signed',
    'archived'
);


SET default_table_access_method = heap;

--
-- Name: admin_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.admin_users (
    id uuid NOT NULL,
    login character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    email character varying(255),
    is_active boolean NOT NULL,
    is_superadmin boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    last_login timestamp with time zone,
    is_commission_eligible boolean DEFAULT false NOT NULL,
    position_title character varying(512)
);


--
-- Name: certificates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.certificates (
    id uuid NOT NULL,
    certificate_number character varying(100) NOT NULL,
    user_id uuid,
    protocol_id uuid,
    participant_id uuid,
    training_type_id uuid,
    full_name character varying(255) NOT NULL,
    organization_name character varying(255),
    "position" character varying(255),
    issued_date date NOT NULL,
    valid_until date,
    is_renewal boolean NOT NULL,
    pdf_path character varying(512),
    qr_code_path character varying(512),
    created_at timestamp with time zone NOT NULL
);


--
-- Name: course_materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.course_materials (
    id uuid NOT NULL,
    course_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    material_type public.materialtype NOT NULL,
    file_path character varying(512),
    url text,
    file_size_bytes integer,
    sort_order integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: courses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.courses (
    id uuid NOT NULL,
    discipline_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    target_positions character varying(255),
    duration_hours integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: disciplines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disciplines (
    id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean NOT NULL
);


--
-- Name: import_rows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_rows (
    id uuid NOT NULL,
    batch_id uuid NOT NULL,
    row_number integer,
    raw_data json,
    normalized_data json,
    status public.importrowstatus NOT NULL,
    error_message text,
    user_id uuid,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: medical_exams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.medical_exams (
    id uuid NOT NULL,
    user_id uuid,
    organization_id uuid,
    full_name character varying(255) NOT NULL,
    birth_date date,
    gender character varying(10),
    workplace character varying(255),
    "position" character varying(255),
    icd10_group text,
    fit_for_work boolean,
    exam_date date,
    source_file character varying(255),
    imported_at timestamp with time zone NOT NULL
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    short_name character varying(100),
    bin character varying(12),
    contact_email character varying(255),
    contact_phone character varying(50),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: position_course_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.position_course_rules (
    id uuid NOT NULL,
    discipline_id uuid NOT NULL,
    position_id uuid,
    position_keyword character varying(255) NOT NULL,
    course_id uuid NOT NULL,
    priority integer NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: positions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.positions (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    name_kz character varying(255),
    category character varying(100),
    is_active boolean NOT NULL
);


--
-- Name: protocol_commission_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.protocol_commission_members (
    id uuid NOT NULL,
    protocol_id uuid NOT NULL,
    admin_user_id uuid,
    full_name character varying(255) NOT NULL,
    position_title character varying(255),
    role public.commissionrole NOT NULL,
    sort_order integer NOT NULL,
    signed_at timestamp with time zone,
    signature_cms text,
    signer_cert_serial character varying(100),
    signer_cert_owner character varying(512),
    signer_cert_valid_from timestamp with time zone,
    signer_cert_valid_to timestamp with time zone
);


--
-- Name: protocol_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.protocol_participants (
    id uuid NOT NULL,
    protocol_id uuid NOT NULL,
    user_id uuid,
    full_name character varying(255) NOT NULL,
    "position" character varying(255),
    education character varying(100),
    result public.participantresult,
    sort_order integer NOT NULL,
    organization_name character varying(255)
);


--
-- Name: protocols; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.protocols (
    id uuid NOT NULL,
    protocol_number character varying(50) NOT NULL,
    organization_id uuid,
    training_type_id uuid,
    exam_date date NOT NULL,
    order_number character varying(100),
    order_date date,
    legal_basis text,
    regulatory_docs text,
    status public.protocolstatus NOT NULL,
    created_by_id uuid,
    created_at timestamp with time zone NOT NULL,
    batch_id uuid,
    check_type public.checktype
);


--
-- Name: test_attempt_answers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.test_attempt_answers (
    id uuid NOT NULL,
    attempt_id uuid NOT NULL,
    question_id uuid NOT NULL,
    selected_option_id uuid,
    is_correct boolean
);


--
-- Name: test_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.test_attempts (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    assignment_id uuid NOT NULL,
    test_id uuid NOT NULL,
    attempt_number integer NOT NULL,
    status public.attemptstatus NOT NULL,
    score integer,
    max_score integer,
    score_percent integer,
    passed boolean,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone
);


--
-- Name: test_question_options; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.test_question_options (
    id uuid NOT NULL,
    question_id uuid NOT NULL,
    text text NOT NULL,
    is_correct boolean NOT NULL,
    sort_order integer NOT NULL
);


--
-- Name: test_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.test_questions (
    id uuid NOT NULL,
    test_id uuid NOT NULL,
    text text NOT NULL,
    image_path character varying(512),
    sort_order integer NOT NULL
);


--
-- Name: tests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tests (
    id uuid NOT NULL,
    course_id uuid NOT NULL,
    pass_score integer NOT NULL,
    max_attempts integer NOT NULL,
    time_limit_minutes integer NOT NULL,
    show_correct_answers boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: training_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_batches (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    organization_id uuid,
    status public.batchstatus NOT NULL,
    excel_file_path character varying(512),
    notes text,
    created_by_id uuid,
    created_at timestamp with time zone NOT NULL,
    confirmed_at timestamp with time zone,
    discipline_ids jsonb DEFAULT '[]'::jsonb
);


--
-- Name: training_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_types (
    id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name_ru character varying(255) NOT NULL,
    name_short character varying(50) NOT NULL,
    validity_years integer NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: user_course_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_course_assignments (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    course_id uuid NOT NULL,
    discipline_id uuid NOT NULL,
    batch_id uuid,
    status public.assignmentstatus NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone
);


--
-- Name: user_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_documents (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    file_path character varying(512) NOT NULL,
    mime_type character varying(100),
    file_size bigint,
    uploaded_at timestamp with time zone NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    login character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    normalized_full_name character varying(255) NOT NULL,
    organization_id uuid,
    position_id uuid,
    position_raw character varying(255),
    batch_id uuid,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    last_login timestamp with time zone,
    plain_password character varying(255),
    verify_token uuid,
    photo_path character varying(512)
);


--
-- Name: admin_users admin_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (id);


--
-- Name: certificates certificates_certificate_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_certificate_number_key UNIQUE (certificate_number);


--
-- Name: certificates certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_pkey PRIMARY KEY (id);


--
-- Name: course_materials course_materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_materials
    ADD CONSTRAINT course_materials_pkey PRIMARY KEY (id);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- Name: disciplines disciplines_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disciplines
    ADD CONSTRAINT disciplines_code_key UNIQUE (code);


--
-- Name: disciplines disciplines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disciplines
    ADD CONSTRAINT disciplines_pkey PRIMARY KEY (id);


--
-- Name: import_rows import_rows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_rows
    ADD CONSTRAINT import_rows_pkey PRIMARY KEY (id);


--
-- Name: medical_exams medical_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.medical_exams
    ADD CONSTRAINT medical_exams_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: position_course_rules position_course_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.position_course_rules
    ADD CONSTRAINT position_course_rules_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: protocol_commission_members protocol_commission_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_commission_members
    ADD CONSTRAINT protocol_commission_members_pkey PRIMARY KEY (id);


--
-- Name: protocol_participants protocol_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_participants
    ADD CONSTRAINT protocol_participants_pkey PRIMARY KEY (id);


--
-- Name: protocols protocols_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_pkey PRIMARY KEY (id);


--
-- Name: test_attempt_answers test_attempt_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempt_answers
    ADD CONSTRAINT test_attempt_answers_pkey PRIMARY KEY (id);


--
-- Name: test_attempts test_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempts
    ADD CONSTRAINT test_attempts_pkey PRIMARY KEY (id);


--
-- Name: test_question_options test_question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_question_options
    ADD CONSTRAINT test_question_options_pkey PRIMARY KEY (id);


--
-- Name: test_questions test_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_questions
    ADD CONSTRAINT test_questions_pkey PRIMARY KEY (id);


--
-- Name: tests tests_course_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tests
    ADD CONSTRAINT tests_course_id_key UNIQUE (course_id);


--
-- Name: tests tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);


--
-- Name: training_batches training_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_batches
    ADD CONSTRAINT training_batches_pkey PRIMARY KEY (id);


--
-- Name: training_types training_types_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_types
    ADD CONSTRAINT training_types_code_key UNIQUE (code);


--
-- Name: training_types training_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_types
    ADD CONSTRAINT training_types_pkey PRIMARY KEY (id);


--
-- Name: user_course_assignments user_course_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_course_assignments
    ADD CONSTRAINT user_course_assignments_pkey PRIMARY KEY (id);


--
-- Name: user_documents user_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_documents
    ADD CONSTRAINT user_documents_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_admin_users_login; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_admin_users_login ON public.admin_users USING btree (login);


--
-- Name: ix_certificates_participant_id_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_certificates_participant_id_unique ON public.certificates USING btree (participant_id) WHERE (participant_id IS NOT NULL);


--
-- Name: ix_certificates_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_certificates_user_id ON public.certificates USING btree (user_id);


--
-- Name: ix_course_materials_course_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_course_materials_course_id ON public.course_materials USING btree (course_id);


--
-- Name: ix_courses_discipline_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_courses_discipline_id ON public.courses USING btree (discipline_id);


--
-- Name: ix_import_rows_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_rows_batch_id ON public.import_rows USING btree (batch_id);


--
-- Name: ix_medical_exams_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_medical_exams_organization_id ON public.medical_exams USING btree (organization_id);


--
-- Name: ix_medical_exams_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_medical_exams_user_id ON public.medical_exams USING btree (user_id);


--
-- Name: ix_position_course_rules_discipline_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_position_course_rules_discipline_id ON public.position_course_rules USING btree (discipline_id);


--
-- Name: ix_protocol_commission_members_protocol_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_protocol_commission_members_protocol_id ON public.protocol_commission_members USING btree (protocol_id);


--
-- Name: ix_protocol_participants_protocol_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_protocol_participants_protocol_id ON public.protocol_participants USING btree (protocol_id);


--
-- Name: ix_protocol_participants_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_protocol_participants_user_id ON public.protocol_participants USING btree (user_id);


--
-- Name: ix_protocols_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_protocols_batch_id ON public.protocols USING btree (batch_id);


--
-- Name: ix_protocols_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_protocols_organization_id ON public.protocols USING btree (organization_id);


--
-- Name: ix_test_attempt_answers_attempt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_attempt_answers_attempt_id ON public.test_attempt_answers USING btree (attempt_id);


--
-- Name: ix_test_attempts_assignment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_attempts_assignment_id ON public.test_attempts USING btree (assignment_id);


--
-- Name: ix_test_attempts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_attempts_user_id ON public.test_attempts USING btree (user_id);


--
-- Name: ix_test_question_options_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_question_options_question_id ON public.test_question_options USING btree (question_id);


--
-- Name: ix_test_questions_test_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_questions_test_id ON public.test_questions USING btree (test_id);


--
-- Name: ix_training_batches_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_batches_organization_id ON public.training_batches USING btree (organization_id);


--
-- Name: ix_user_course_assignments_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_course_assignments_batch_id ON public.user_course_assignments USING btree (batch_id);


--
-- Name: ix_user_course_assignments_course_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_course_assignments_course_id ON public.user_course_assignments USING btree (course_id);


--
-- Name: ix_user_course_assignments_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_course_assignments_user_id ON public.user_course_assignments USING btree (user_id);


--
-- Name: ix_user_documents_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_documents_user_id ON public.user_documents USING btree (user_id);


--
-- Name: ix_users_login; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_login ON public.users USING btree (login);


--
-- Name: ix_users_normalized_full_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_normalized_full_name ON public.users USING btree (normalized_full_name);


--
-- Name: ix_users_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_organization_id ON public.users USING btree (organization_id);


--
-- Name: ix_users_verify_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_verify_token ON public.users USING btree (verify_token);


--
-- Name: certificates certificates_participant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES public.protocol_participants(id) ON DELETE SET NULL;


--
-- Name: certificates certificates_protocol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_protocol_id_fkey FOREIGN KEY (protocol_id) REFERENCES public.protocols(id) ON DELETE SET NULL;


--
-- Name: certificates certificates_training_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_training_type_id_fkey FOREIGN KEY (training_type_id) REFERENCES public.training_types(id) ON DELETE SET NULL;


--
-- Name: certificates certificates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: course_materials course_materials_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_materials
    ADD CONSTRAINT course_materials_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: courses courses_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.disciplines(id) ON DELETE RESTRICT;


--
-- Name: import_rows import_rows_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_rows
    ADD CONSTRAINT import_rows_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.training_batches(id) ON DELETE CASCADE;


--
-- Name: import_rows import_rows_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_rows
    ADD CONSTRAINT import_rows_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: medical_exams medical_exams_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.medical_exams
    ADD CONSTRAINT medical_exams_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: medical_exams medical_exams_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.medical_exams
    ADD CONSTRAINT medical_exams_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: position_course_rules position_course_rules_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.position_course_rules
    ADD CONSTRAINT position_course_rules_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: position_course_rules position_course_rules_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.position_course_rules
    ADD CONSTRAINT position_course_rules_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.disciplines(id) ON DELETE CASCADE;


--
-- Name: position_course_rules position_course_rules_position_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.position_course_rules
    ADD CONSTRAINT position_course_rules_position_id_fkey FOREIGN KEY (position_id) REFERENCES public.positions(id) ON DELETE SET NULL;


--
-- Name: protocol_commission_members protocol_commission_members_admin_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_commission_members
    ADD CONSTRAINT protocol_commission_members_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.admin_users(id) ON DELETE SET NULL;


--
-- Name: protocol_commission_members protocol_commission_members_protocol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_commission_members
    ADD CONSTRAINT protocol_commission_members_protocol_id_fkey FOREIGN KEY (protocol_id) REFERENCES public.protocols(id) ON DELETE CASCADE;


--
-- Name: protocol_participants protocol_participants_protocol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_participants
    ADD CONSTRAINT protocol_participants_protocol_id_fkey FOREIGN KEY (protocol_id) REFERENCES public.protocols(id) ON DELETE CASCADE;


--
-- Name: protocol_participants protocol_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocol_participants
    ADD CONSTRAINT protocol_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: protocols protocols_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.training_batches(id) ON DELETE SET NULL;


--
-- Name: protocols protocols_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.admin_users(id) ON DELETE SET NULL;


--
-- Name: protocols protocols_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: protocols protocols_training_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_training_type_id_fkey FOREIGN KEY (training_type_id) REFERENCES public.training_types(id) ON DELETE SET NULL;


--
-- Name: test_attempt_answers test_attempt_answers_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempt_answers
    ADD CONSTRAINT test_attempt_answers_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.test_attempts(id) ON DELETE CASCADE;


--
-- Name: test_attempt_answers test_attempt_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempt_answers
    ADD CONSTRAINT test_attempt_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.test_questions(id) ON DELETE CASCADE;


--
-- Name: test_attempt_answers test_attempt_answers_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempt_answers
    ADD CONSTRAINT test_attempt_answers_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.test_question_options(id) ON DELETE SET NULL;


--
-- Name: test_attempts test_attempts_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempts
    ADD CONSTRAINT test_attempts_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.user_course_assignments(id) ON DELETE CASCADE;


--
-- Name: test_attempts test_attempts_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempts
    ADD CONSTRAINT test_attempts_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.tests(id) ON DELETE CASCADE;


--
-- Name: test_attempts test_attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_attempts
    ADD CONSTRAINT test_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: test_question_options test_question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_question_options
    ADD CONSTRAINT test_question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.test_questions(id) ON DELETE CASCADE;


--
-- Name: test_questions test_questions_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_questions
    ADD CONSTRAINT test_questions_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.tests(id) ON DELETE CASCADE;


--
-- Name: tests tests_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tests
    ADD CONSTRAINT tests_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: training_batches training_batches_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_batches
    ADD CONSTRAINT training_batches_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.admin_users(id) ON DELETE SET NULL;


--
-- Name: training_batches training_batches_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_batches
    ADD CONSTRAINT training_batches_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: user_course_assignments user_course_assignments_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_course_assignments
    ADD CONSTRAINT user_course_assignments_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.training_batches(id) ON DELETE SET NULL;


--
-- Name: user_course_assignments user_course_assignments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_course_assignments
    ADD CONSTRAINT user_course_assignments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;


--
-- Name: user_course_assignments user_course_assignments_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_course_assignments
    ADD CONSTRAINT user_course_assignments_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.disciplines(id) ON DELETE RESTRICT;


--
-- Name: user_course_assignments user_course_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_course_assignments
    ADD CONSTRAINT user_course_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_documents user_documents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_documents
    ADD CONSTRAINT user_documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.training_batches(id) ON DELETE SET NULL;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: users users_position_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_position_id_fkey FOREIGN KEY (position_id) REFERENCES public.positions(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--


